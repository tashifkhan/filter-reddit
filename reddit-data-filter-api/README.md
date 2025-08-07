# Reddit Data Filter API

A FastAPI-based web service for fetching Reddit posts and comments using the Reddit API with user authentication for higher rate limits.

## Features

- **User Authentication**: Use your Reddit credentials for higher rate limits
- **Subreddit Posts**: Fetch posts from any subreddit with various sorting options
- **Comments Extraction**: Get all comments for specific posts with full thread expansion
- **Multiple Data Sources**: Support for both official Reddit API and Pushshift API
- **Rate Limiting**: Built-in rate limiting and API politeness
- **Comprehensive Models**: Well-structured Pydantic models for all responses

## Setup

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 2. Reddit API Configuration

1. Go to https://www.reddit.com/prefs/apps
2. Create a new "script" type app (not web app)
3. Note down your `client_id` and `client_secret`

### 3. Environment Variables

Create a `.env` file in the project root with your Reddit API credentials:

```env
# Reddit API Credentials (from your script app)
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here

# Your Reddit User Credentials (for higher rate limits)
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password

# User Agent (recommended)
REDDIT_USER_AGENT=web:reddit-data-filter:v1.0 (by u/your_reddit_username)
```

### 4. Run the Application

```bash
# Using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or using Python
python main.py
```

The API will be available at: http://localhost:8000

Interactive API documentation: http://localhost:8000/docs

## API Endpoints

### Core

- `GET /` - API information and links

### Reddit Data

- `GET /subreddit/{subreddit_name}/posts` - Get posts from a subreddit
  - Parameters: `listing` (new/hot/top/rising/controversial), `limit`, `use_user_auth` (boolean)
- `GET /submission/{submission_id}` - Get a single post
  - Parameters: `use_user_auth` (boolean)
- `GET /submission/{submission_id}/comments` - Get post with all comments
  - Parameters: `replace_more_limit`, `use_user_auth` (boolean)

### Pushshift API (Historical Data)

- `GET /pushshift/subreddit/{subreddit_name}/posts` - Get historical posts
  - Parameters: `before`, `after`, `size`
- `GET /pushshift/submission/{submission_id}/comments` - Get historical comments

### Utility

- `GET /health` - Health check endpoint

## Usage Examples

### 1. Basic Usage (App-only Authentication)

```python
import requests

# Get latest posts from r/python (lower rate limits)
response = requests.get("http://localhost:8000/subreddit/python/posts?limit=10")
posts = response.json()

print(f"Found {posts['count']} posts")
for post in posts['posts']:
    print(f"- {post['title']} (Score: {post['score']})")
```

### 2. With User Authentication (Higher Rate Limits)

```python
import requests

# Get posts with user authentication (higher rate limits)
response = requests.get(
    "http://localhost:8000/subreddit/python/posts?use_user_auth=true&limit=5"
)
posts = response.json()

# Get a post with all comments using user auth
post_id = posts['posts'][0]['id']
response = requests.get(
    f"http://localhost:8000/submission/{post_id}/comments?use_user_auth=true"
)
post_with_comments = response.json()

print(f"Post: {post_with_comments['post']['title']}")
print(f"Comments: {len(post_with_comments['comments'])}")
```

### 3. Historical Data with Pushshift

```python
import requests
import time

# Get historical posts from last week
week_ago = int(time.time()) - (7 * 24 * 60 * 60)

response = requests.get(
    f"http://localhost:8000/pushshift/subreddit/python/posts?after={week_ago}&size=100"
)
historical_posts = response.json()

print(f"Found {historical_posts['count']} historical posts")
```

## Response Models

### PostData

- `id`: Post ID
- `title`: Post title
- `author`: Author username
- `subreddit`: Subreddit name
- `score`: Post score (upvotes - downvotes)
- `upvote_ratio`: Ratio of upvotes
- `num_comments`: Number of comments
- `created_utc`: Creation timestamp
- `url`: External URL (if link post)
- `permalink`: Reddit permalink
- `selftext`: Post text content
- `is_self`: Whether it's a text post
- `over_18`: NSFW flag
- `link_flair_text`: Post flair
- `stickied`: Whether post is stickied

### CommentData

- `id`: Comment ID
- `parent_id`: Parent comment/post ID
- `link_id`: Associated post ID
- `author`: Comment author
- `body`: Comment text
- `score`: Comment score
- `created_utc`: Creation timestamp
- `permalink`: Comment permalink
- `is_submitter`: Whether commenter is post author
- `distinguished`: Moderator/admin status
- `stickied`: Whether comment is stickied
- `controversiality`: Controversy score
- `depth`: Nesting depth in thread

## Rate Limiting

The API includes built-in rate limiting:

- 0.1 second delay between Reddit API requests
- 0.5 second delay between Pushshift API requests
- Automatic handling of Reddit API rate limits via PRAW

## Security Notes

- User credentials are stored in environment variables (use secure credential management in production)
- CORS is enabled for all origins (configure for production)
- No persistent storage of user data
- Consider using environment-specific credential management for production

## Production Deployment

For production use:

1. **Database**: Replace in-memory storage with proper database
2. **Security**: Configure CORS origins, add HTTPS
3. **Monitoring**: Add logging, metrics, and health checks
4. **Scaling**: Consider Redis for session storage
5. **Rate Limiting**: Implement proper rate limiting middleware

## License

MIT License - see LICENSE file for details
