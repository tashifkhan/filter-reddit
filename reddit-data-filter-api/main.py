import os
import time
from typing import Dict, Any, List, Optional, Iterator

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import praw
from praw.models import Submission, Comment
from praw.models.reddit.more import MoreComments
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Reddit Data Filter API",
    description="API for fetching Reddit posts and comments with OAuth authentication",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")

# For user-specific authentication (script type app)
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")

USER_AGENT = os.getenv(
    "REDDIT_USER_AGENT",
    "web:reddit-data-filter:v1.0 (by u/yourusername)",
)

# Configuration for user authentication


# Pydantic models
class PostData(BaseModel):
    id: str
    title: str
    author: Optional[str]
    subreddit: str
    score: int
    upvote_ratio: float
    num_comments: int
    created_utc: float
    url: str
    permalink: str
    selftext: str
    is_self: bool
    over_18: bool
    link_flair_text: Optional[str]
    stickied: bool


class CommentData(BaseModel):
    id: str
    parent_id: str
    link_id: str
    author: Optional[str]
    body: str
    score: int
    created_utc: float
    permalink: str
    is_submitter: bool
    distinguished: Optional[str]
    stickied: bool
    controversiality: int
    depth: Optional[int]


class PostWithComments(BaseModel):
    post: PostData
    comments: List[CommentData]


class PostsResponse(BaseModel):
    posts: List[PostData]
    count: int


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# Helper functions
def get_reddit_client() -> praw.Reddit:
    """Get Reddit client for app-only access"""
    return praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT,
    )


def get_reddit_client_for_user() -> praw.Reddit:
    """Get Reddit client for user-authenticated access"""
    return praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        username=REDDIT_USERNAME,
        password=REDDIT_PASSWORD,
        user_agent=USER_AGENT,
    )


def submission_to_dict(s: Submission) -> Dict[str, Any]:
    """Convert PRAW Submission to dictionary"""
    return {
        "id": s.id,
        "title": s.title,
        "author": str(s.author) if s.author else None,
        "subreddit": str(s.subreddit),
        "score": s.score,
        "upvote_ratio": s.upvote_ratio,
        "num_comments": s.num_comments,
        "created_utc": s.created_utc,
        "url": s.url,
        "permalink": f"https://reddit.com{s.permalink}",
        "selftext": s.selftext,
        "is_self": s.is_self,
        "over_18": s.over_18,
        "link_flair_text": s.link_flair_text,
        "stickied": s.stickied,
    }


def comment_to_dict(c: Comment) -> Dict[str, Any]:
    """Convert PRAW Comment to dictionary"""
    return {
        "id": c.id,
        "parent_id": c.parent_id,
        "link_id": c.link_id,
        "author": str(c.author) if c.author else None,
        "body": c.body,
        "score": c.score,
        "created_utc": c.created_utc,
        "permalink": f"https://reddit.com{c.permalink}",
        "is_submitter": c.is_submitter,
        "distinguished": c.distinguished,
        "stickied": c.stickied,
        "controversiality": c.controversiality,
        "depth": getattr(c, "depth", None),
    }


def yield_submissions(
    subreddit_name: str,
    listing: str = "new",
    limit: Optional[int] = None,
    use_user_auth: bool = False,
) -> Iterator[Submission]:
    """Yield submissions from a subreddit"""
    if use_user_auth:
        reddit = get_reddit_client_for_user()
    else:
        reddit = get_reddit_client()

    subreddit = reddit.subreddit(subreddit_name)

    if listing == "new":
        generator = subreddit.new(limit=limit)
    elif listing == "hot":
        generator = subreddit.hot(limit=limit)
    elif listing == "top":
        generator = subreddit.top(limit=limit)
    elif listing == "rising":
        generator = subreddit.rising(limit=limit)
    elif listing == "controversial":
        generator = subreddit.controversial(limit=limit)
    else:
        raise ValueError("listing must be one of new/hot/top/rising/controversial")

    for submission in generator:
        yield submission
        time.sleep(0.1)  # Be gentle with API


# API endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Reddit Data Filter API",
        "version": "1.0.0",
        "docs": "/docs",
    }


# Reddit data endpoints
@app.get("/subreddit/{subreddit_name}/posts", response_model=PostsResponse)
async def get_subreddit_posts(
    subreddit_name: str,
    listing: str = Query("new", pattern="^(new|hot|top|rising|controversial)$"),
    limit: Optional[int] = Query(100, ge=1, le=1000),
    use_user_auth: bool = Query(
        False,
        description="Use user authentication for higher rate limits",
    ),
):
    """Get posts from a subreddit"""
    try:
        posts = []

        for submission in yield_submissions(
            subreddit_name, listing, limit, use_user_auth
        ):
            posts.append(PostData(**submission_to_dict(submission)))

        return PostsResponse(posts=posts, count=len(posts))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch posts: {str(e)}",
        )


@app.get("/submission/{submission_id}/comments", response_model=PostWithComments)
async def get_submission_with_comments(
    submission_id: str,
    replace_more_limit: Optional[int] = Query(
        None,
        description="Limit for replacing MoreComments objects",
    ),
    use_user_auth: bool = Query(
        False,
        description="Use user authentication for higher rate limits",
    ),
):
    """Get a submission with all its comments"""
    try:
        if use_user_auth:
            reddit = get_reddit_client_for_user()
        else:
            reddit = get_reddit_client()

        # Get submission
        submission = reddit.submission(id=submission_id)

        # Expand comments
        submission.comments.replace_more(limit=replace_more_limit)
        flat_comments = submission.comments.list()

        # Convert to response format
        post_data = PostData(**submission_to_dict(submission))
        comments_data = []

        for comment in flat_comments:
            if isinstance(comment, MoreComments):
                continue
            comments_data.append(CommentData(**comment_to_dict(comment)))

        return PostWithComments(post=post_data, comments=comments_data)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch submission with comments: {str(e)}",
        )


@app.get("/submission/{submission_id}", response_model=PostData)
async def get_submission(
    submission_id: str,
    use_user_auth: bool = Query(
        False,
        description="Use user authentication for higher rate limits",
    ),
):
    """Get a single submission without comments"""
    try:
        if use_user_auth:
            reddit = get_reddit_client_for_user()
        else:
            reddit = get_reddit_client()

        submission = reddit.submission(id=submission_id)
        return PostData(**submission_to_dict(submission))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch submission: {str(e)}",
        )


# Pushshift endpoints (alternative data source)
@app.get("/pushshift/subreddit/{subreddit_name}/posts")
async def get_pushshift_posts(
    subreddit_name: str,
    before: Optional[int] = Query(
        None,
        description="UNIX timestamp - fetch posts before this time",
    ),
    after: Optional[int] = Query(
        None,
        description="UNIX timestamp - fetch posts after this time",
    ),
    size: int = Query(500, ge=1, le=500, description="Number of posts to fetch"),
):
    """Get posts from Pushshift API (historical data)"""
    try:
        url = "https://api.pushshift.io/reddit/search/submission"
        params = {
            "subreddit": subreddit_name,
            "size": size,
            "sort": "desc",
            "sort_type": "created_utc",
        }
        if before is not None:
            params["before"] = before
        if after is not None:
            params["after"] = after

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json().get("data", [])

        return {"posts": data, "count": len(data)}

    except requests.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch from Pushshift: {str(e)}",
        )


@app.get("/pushshift/submission/{submission_id}/comments")
async def get_pushshift_comments(
    submission_id: str,
    size: int = Query(
        500,
        ge=1,
        le=500,
        description="Number of comments to fetch per request",
    ),
):
    """Get comments for a submission from Pushshift API"""
    try:
        url = "https://api.pushshift.io/reddit/comment/search"
        params = {
            "link_id": f"t3_{submission_id}",
            "size": size,
            "sort": "asc",
            "sort_type": "created_utc",
        }

        all_comments = []
        last_timestamp = None

        while True:
            if last_timestamp is not None:
                params["after"] = last_timestamp + 1

            response = requests.get(
                url,
                params=params,
                timeout=30,
            )

            response.raise_for_status()
            data = response.json().get("data", [])

            if not data:
                break

            all_comments.extend(data)
            last_timestamp = data[-1]["created_utc"]
            time.sleep(0.5)  # Be gentle with API

        return {
            "comments": all_comments,
            "count": len(all_comments),
        }

    except requests.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch comments from Pushshift: {str(e)}",
        )


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
