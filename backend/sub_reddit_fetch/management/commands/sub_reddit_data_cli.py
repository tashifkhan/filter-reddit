import logging
from django.core.management.base import BaseCommand, CommandError
from sub_reddit_fetch.tasks.run_sub_reddit_data import fetch_sub_reddit_data

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Fetch data from subreddits and queue them to Kafka via Celery"

    def add_arguments(self, parser):
        parser.add_argument('user_query', type=str, help='User query for filtering')
        parser.add_argument('--sub_reddit_names', type=str, nargs='+', required=True, help='List of subreddit names')
        parser.add_argument('--duration', type=int, required=True, help='Duration in days')
        parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    def handle(self, *args, **options):
        user_query = options['user_query']
        sub_reddit_names = options['sub_reddit_names']
        duration = options['duration']
        
        if options.get('debug', False):
            logger.setLevel(logging.DEBUG)
        
        logger.info(f"Starting to process {len(sub_reddit_names)} subreddits")
        logger.info(f"User query: {user_query}")
        logger.info(f"Duration: {duration} days")
        
        # Queue each subreddit to Celery
        for sub_reddit_name in sub_reddit_names:
            try:
                logger.info(f"Queuing task for subreddit: {sub_reddit_name}")
                
                # Queue the Celery task
                task = fetch_sub_reddit_data.delay(sub_reddit_name, duration)
                
                logger.info(f"Successfully queued task for {sub_reddit_name}. Task ID: {task.id}")
                
            except Exception as e:
                logger.error(f"Error queuing task for subreddit {sub_reddit_name}: {str(e)}", exc_info=True)
                raise CommandError(f"Failed to queue task for subreddit {sub_reddit_name}: {e}")
        
        logger.info(f"Successfully queued all {len(sub_reddit_names)} subreddit tasks to Celery")
        self.stdout.write(
            self.style.SUCCESS(f'Successfully queued {len(sub_reddit_names)} subreddit tasks to Celery')
        ) 
