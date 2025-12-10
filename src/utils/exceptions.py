"""Custom exception classes for the YouTube Shorts automation system."""


class YouTubeShortsError(Exception):
    """Base exception for all YouTube Shorts automation errors."""
    pass


class VideoDiscoveryError(YouTubeShortsError):
    """Exception raised during video discovery phase."""
    pass


class URLValidationError(VideoDiscoveryError):
    """Exception raised when URL validation fails."""
    pass


class AnalysisError(YouTubeShortsError):
    """Exception raised during AI analysis phase."""
    pass


class GeminiAPIError(AnalysisError):
    """Exception raised for Gemini API related errors."""
    pass


class SceneAnalysisError(AnalysisError):
    """Exception raised during scene analysis."""
    pass


class GenerationError(YouTubeShortsError):
    """Exception raised during video generation phase."""
    pass


class SoraAPIError(GenerationError):
    """Exception raised for Sora API related errors."""
    pass


class VideoDownloadError(GenerationError):
    """Exception raised when video download fails."""
    pass


class ProcessingError(YouTubeShortsError):
    """Exception raised during video processing phase."""
    pass


class WatermarkRemovalError(ProcessingError):
    """Exception raised during watermark removal."""
    pass


class VideoOptimizationError(ProcessingError):
    """Exception raised during video optimization."""
    pass


class PublishingError(YouTubeShortsError):
    """Exception raised during publishing phase."""
    pass


class UploadError(PublishingError):
    """Exception raised during video upload."""
    pass


class PlatformAPIError(PublishingError):
    """Exception raised for platform API related errors."""
    pass


class AuthenticationError(PublishingError):
    """Exception raised for authentication failures."""
    pass


class DatabaseError(YouTubeShortsError):
    """Exception raised for database related errors."""
    pass


class ConfigurationError(YouTubeShortsError):
    """Exception raised for configuration related errors."""
    pass


class WorkflowError(YouTubeShortsError):
    """Exception raised for workflow/pipeline errors."""
    pass


class RateLimitError(YouTubeShortsError):
    """Exception raised when rate limit is exceeded."""
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after


class TimeoutError(YouTubeShortsError):
    """Exception raised when an operation times out."""
    pass


class ValidationError(YouTubeShortsError):
    """Exception raised for data validation errors."""
    pass
