# Reddit Data Filter API

A FastAPI-based web service for fetching Reddit posts and comments using the Reddit API with OAuth authentication support.

## Features

- **OAuth Authentication**: Secure user authentication with Reddit
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
2. Create a new "web app"
3. Set the redirect URI to: `http://localhost:8000/oauth/callback`
4. Note down your `client_id` and `client_secret`

### 3. Environment Variables

Copy `.env.example` to `.env` and fill in your Reddit API credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Reddit API credentials:

```env
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_REDIRECT_URI=http://localhost:8000/oauth/callback
REDDIT_USER_AGENT=web:reddit-data-filter:v1.0 (by u/yourusername)
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

### Authentication

- `GET /` - API information and links
- `GET /login` - Initiate Reddit OAuth login
- `GET /oauth/callback` - Handle OAuth callback (automatic)
- `GET /me?username={username}` - Get authenticated user info

### Reddit Data

- `GET /subreddit/{subreddit_name}/posts` - Get posts from a subreddit
  - Parameters: `listing` (new/hot/top/rising/controversial), `limit`, `username`
- `GET /submission/{submission_id}` - Get a single post
- `GET /submission/{submission_id}/comments` - Get post with all comments
  - Parameters: `replace_more_limit`, `username`

### Pushshift API (Historical Data)

- `GET /pushshift/subreddit/{subreddit_name}/posts` - Get historical posts
  - Parameters: `before`, `after`, `size`
- `GET /pushshift/submission/{submission_id}/comments` - Get historical comments

### Utility

- `GET /health` - Health check endpoint

## Usage Examples

### 1. Basic Usage (No Authentication)

```python
import requests

# Get latest posts from r/python
response = requests.get("http://localhost:8000/subreddit/python/posts?limit=10")
posts = response.json()

print(f"Found {posts['count']} posts")
for post in posts['posts']:
    print(f"- {post['title']} (Score: {post['score']})")
```

### 2. With Authentication

```python
import requests

# First, authenticate by visiting http://localhost:8000/login in browser
# After authentication, use your Reddit username in requests

username = "your_reddit_username"

# Get posts with user authentication
response = requests.get(
    f"http://localhost:8000/subreddit/python/posts?username={username}&limit=5"
)
posts = response.json()

# Get a post with all comments
post_id = posts['posts'][0]['id']
response = requests.get(
    f"http://localhost:8000/submission/{post_id}/comments?username={username}"
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

- OAuth state validation prevents CSRF attacks
- Refresh tokens are stored in memory (use database in production)
- CORS is enabled for all origins (configure for production)
- No persistent storage of user data

## Production Deployment

For production use:

1. **Database**: Replace in-memory storage with proper database
2. **Security**: Configure CORS origins, add HTTPS
3. **Monitoring**: Add logging, metrics, and health checks
4. **Scaling**: Consider Redis for session storage
5. **Rate Limiting**: Implement proper rate limiting middleware

## License

MIT License - see LICENSE file for details
