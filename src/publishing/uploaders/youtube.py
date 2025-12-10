"""YouTube uploader for publishing videos."""

import os
import pickle
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from ...utils.config import config
from ...utils.logger import get_publishing_logger
from ...utils.exceptions import UploadError, AuthenticationError
from ...storage.database import get_session
from ...storage.models import PublishRecord, Platform

logger = get_publishing_logger(__name__)


class YouTubeUploader:
    """Upload videos to YouTube using the Data API v3."""
    
    # YouTube API scopes
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    
    def __init__(self):
        """Initialize YouTube uploader."""
        self.credentials = None
        self.youtube = None
        self._authenticate()
        logger.info("YouTube uploader initialized")
    
    def _authenticate(self):
        """Authenticate with YouTube API using OAuth2."""
        token_file = config.project_root / "youtube_token.pickle"
        credentials_file = config.project_root / "youtube_credentials.json"
        
        # Load saved credentials if available
        if token_file.exists():
            logger.info("Loading saved YouTube credentials")
            with open(token_file, 'rb') as token:
                self.credentials = pickle.load(token)
        
        # If credentials are invalid or don't exist, get new ones
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                logger.info("Refreshing YouTube credentials")
                self.credentials.refresh(Request())
            else:
                if not credentials_file.exists():
                    raise AuthenticationError(
                        f"YouTube OAuth credentials file not found: {credentials_file}\n"
                        "Please download OAuth 2.0 credentials from Google Cloud Console"
                    )
                
                logger.info("Initiating new OAuth flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_file),
                    self.SCOPES
                )
                self.credentials = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(token_file, 'wb') as token:
                pickle.dump(self.credentials, token)
            logger.info("YouTube credentials saved")
        
        # Build YouTube service
        self.youtube = build('youtube', 'v3', credentials=self.credentials)
        logger.info("YouTube API service built successfully")
    
    def upload_video(
        self,
        video_file_path: Path,
        title: str,
        description: str,
        tags: Optional[list] = None,
        category_id: str = "22",
        privacy_status: str = "public",
        made_for_kids: bool = False,
        notify_subscribers: bool = True
    ) -> Dict:
        """Upload a video to YouTube.
        
        Args:
            video_file_path: Path to video file
            title: Video title
            description: Video description
            tags: List of tags
            category_id: YouTube category ID (default: 22 = People & Blogs)
            privacy_status: Privacy status (public, private, unlisted)
            made_for_kids: Whether video is made for kids
            notify_subscribers: Whether to notify subscribers
            
        Returns:
            Dictionary with upload result including video ID and URL
            
        Raises:
            UploadError: If upload fails
        """
        if not video_file_path.exists():
            raise UploadError(f"Video file not found: {video_file_path}")
        
        logger.info(f"Uploading video: {video_file_path.name}")
        logger.info(f"Title: {title[:50]}...")
        
        # Prepare video metadata
        body = {
            'snippet': {
                'title': title[:100],  # YouTube max: 100 chars
                'description': description[:5000],  # YouTube max: 5000 chars
                'tags': tags[:500] if tags else [],  # YouTube max: 500 chars total
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': made_for_kids,
                'notifySubscribers': notify_subscribers
            }
        }
        
        # Create media upload
        media = MediaFileUpload(
            str(video_file_path),
            chunksize=-1,
            resumable=True,
            mimetype='video/*'
        )
        
        try:
            # Execute upload
            request = self.youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"Upload progress: {progress}%")
            
            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            logger.info(f"✓ Upload successful!")
            logger.info(f"  Video ID: {video_id}")
            logger.info(f"  URL: {video_url}")
            
            return {
                'success': True,
                'video_id': video_id,
                'url': video_url,
                'title': title,
                'privacy_status': privacy_status,
                'uploaded_at': datetime.utcnow().isoformat()
            }
        
        except HttpError as e:
            error_msg = f"YouTube API error: {e}"
            logger.error(error_msg)
            raise UploadError(error_msg)
        
        except Exception as e:
            error_msg = f"Upload failed: {e}"
            logger.error(error_msg)
            raise UploadError(error_msg)
    
    def upload_short(
        self,
        video_file_path: Path,
        title: str,
        description: str,
        tags: Optional[list] = None,
        privacy_status: str = "public"
    ) -> Dict:
        """Upload a YouTube Short.
        
        This is a convenience method specifically for Shorts.
        
        Args:
            video_file_path: Path to video file
            title: Video title
            description: Video description
            tags: List of tags
            privacy_status: Privacy status
            
        Returns:
            Dictionary with upload result
        """
        logger.info("Uploading as YouTube Short")
        
        # Ensure #Shorts tag is included
        if tags:
            if '#Shorts' not in tags and '#shorts' not in tags:
                tags.insert(0, '#Shorts')
        else:
            tags = ['#Shorts']
        
        # Add #Shorts to description if not present
        if '#Shorts' not in description and '#shorts' not in description:
            description = description + "\n\n#Shorts"
        
        return self.upload_video(
            video_file_path=video_file_path,
            title=title,
            description=description,
            tags=tags,
            category_id="22",  # People & Blogs
            privacy_status=privacy_status,
            made_for_kids=False,
            notify_subscribers=True
        )
    
    def update_video_metadata(
        self,
        video_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list] = None,
        privacy_status: Optional[str] = None
    ) -> bool:
        """Update metadata for an existing video.
        
        Args:
            video_id: YouTube video ID
            title: New title (optional)
            description: New description (optional)
            tags: New tags (optional)
            privacy_status: New privacy status (optional)
            
        Returns:
            True if successful
            
        Raises:
            UploadError: If update fails
        """
        logger.info(f"Updating metadata for video: {video_id}")
        
        try:
            # Get current video metadata
            request = self.youtube.videos().list(
                part='snippet,status',
                id=video_id
            )
            response = request.execute()
            
            if not response.get('items'):
                raise UploadError(f"Video not found: {video_id}")
            
            video = response['items'][0]
            
            # Update fields
            if title:
                video['snippet']['title'] = title[:100]
            if description:
                video['snippet']['description'] = description[:5000]
            if tags:
                video['snippet']['tags'] = tags[:500]
            if privacy_status:
                video['status']['privacyStatus'] = privacy_status
            
            # Update video
            update_request = self.youtube.videos().update(
                part='snippet,status',
                body=video
            )
            update_request.execute()
            
            logger.info(f"✓ Metadata updated for video: {video_id}")
            return True
        
        except HttpError as e:
            error_msg = f"Failed to update video metadata: {e}"
            logger.error(error_msg)
            raise UploadError(error_msg)
    
    def delete_video(self, video_id: str) -> bool:
        """Delete a video from YouTube.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            True if successful
            
        Raises:
            UploadError: If deletion fails
        """
        logger.info(f"Deleting video: {video_id}")
        
        try:
            request = self.youtube.videos().delete(id=video_id)
            request.execute()
            
            logger.info(f"✓ Video deleted: {video_id}")
            return True
        
        except HttpError as e:
            error_msg = f"Failed to delete video: {e}"
            logger.error(error_msg)
            raise UploadError(error_msg)
    
    def get_video_stats(self, video_id: str) -> Dict:
        """Get statistics for a video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Dictionary with video statistics
            
        Raises:
            UploadError: If request fails
        """
        try:
            request = self.youtube.videos().list(
                part='statistics,snippet',
                id=video_id
            )
            response = request.execute()
            
            if not response.get('items'):
                raise UploadError(f"Video not found: {video_id}")
            
            video = response['items'][0]
            stats = video.get('statistics', {})
            
            return {
                'video_id': video_id,
                'title': video['snippet']['title'],
                'views': int(stats.get('viewCount', 0)),
                'likes': int(stats.get('likeCount', 0)),
                'comments': int(stats.get('commentCount', 0)),
                'published_at': video['snippet']['publishedAt']
            }
        
        except HttpError as e:
            error_msg = f"Failed to get video stats: {e}"
            logger.error(error_msg)
            raise UploadError(error_msg)
    
    def record_upload_to_database(
        self,
        generated_video_id: int,
        upload_result: Dict,
        metadata: Dict
    ) -> int:
        """Record upload to database.
        
        Args:
            generated_video_id: Generated video ID from database
            upload_result: Upload result dictionary
            metadata: Video metadata
            
        Returns:
            Publish record ID
        """
        with get_session() as session:
            record = PublishRecord(
                generated_video_id=generated_video_id,
                platform=Platform.YOUTUBE,
                platform_video_id=upload_result['video_id'],
                platform_url=upload_result['url'],
                title=metadata['title'],
                description=metadata.get('description', ''),
                tags=metadata.get('tags', []),
                is_published=True,
                published_at=datetime.utcnow()
            )
            
            session.add(record)
            session.flush()
            
            logger.info(f"Upload recorded to database (ID: {record.id})")
            return record.id


def upload_to_youtube(
    video_file_path: Path,
    title: str,
    description: str,
    tags: Optional[list] = None,
    privacy_status: str = "public"
) -> Dict:
    """Convenience function to upload a video to YouTube.
    
    Args:
        video_file_path: Path to video file
        title: Video title
        description: Video description
        tags: List of tags
        privacy_status: Privacy status
        
    Returns:
        Upload result dictionary
    """
    uploader = YouTubeUploader()
    return uploader.upload_short(video_file_path, title, description, tags, privacy_status)
