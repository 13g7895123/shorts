"""Metadata builder for generating video titles, descriptions, and tags."""

from typing import Dict, List, Optional
from datetime import datetime

from ..analysis.gemini_client import GeminiClient
from ..utils.logger import get_publishing_logger
from ..utils.exceptions import PublishingError

logger = get_publishing_logger(__name__)


class MetadataBuilder:
    """Build optimized metadata for video publishing."""
    
    def __init__(self):
        """Initialize metadata builder."""
        self.client = GeminiClient()
        logger.info("Metadata builder initialized")
    
    def generate_title(
        self,
        content_description: str,
        max_length: int = 100,
        style: str = "engaging"
    ) -> str:
        """Generate an optimized video title.
        
        Args:
            content_description: Description of video content
            max_length: Maximum title length
            style: Title style (engaging, descriptive, clickbait, professional)
            
        Returns:
            Generated title
        """
        logger.info(f"Generating title with style: {style}")
        
        style_instructions = {
            'engaging': 'Create an engaging, attention-grabbing title',
            'descriptive': 'Create a clear, descriptive title',
            'clickbait': 'Create an exciting, curiosity-inducing title',
            'professional': 'Create a professional, informative title'
        }
        
        instruction = style_instructions.get(style, style_instructions['engaging'])
        
        prompt = f"""
{instruction} for a YouTube Short based on this content:

{content_description}

Requirements:
- Maximum {max_length} characters
- Optimize for YouTube SEO
- Include relevant keywords
- Make it compelling for viewers
- Use title case

Return ONLY the title, no additional text.
"""
        
        title = self.client.generate_text(prompt).strip()
        
        # Ensure max length
        if len(title) > max_length:
            title = title[:max_length-3] + "..."
        
        logger.info(f"Generated title: {title[:50]}...")
        return title
    
    def generate_description(
        self,
        content_description: str,
        title: str,
        max_length: int = 5000,
        include_cta: bool = True
    ) -> str:
        """Generate an optimized video description.
        
        Args:
            content_description: Description of video content
            title: Video title
            max_length: Maximum description length
            include_cta: Include call-to-action
            
        Returns:
            Generated description
        """
        logger.info("Generating video description")
        
        cta_text = ""
        if include_cta:
            cta_text = """

Don't forget to:
👍 Like this video
💬 Comment your thoughts
🔔 Subscribe for more content
📱 Share with friends
"""
        
        prompt = f"""
Create a compelling YouTube Short description based on this video:

Title: {title}

Content: {content_description}

Requirements:
- Maximum {max_length} characters
- Engaging opening line
- Brief content summary
- SEO-optimized with relevant keywords
- Include relevant emojis
- Natural and conversational tone
{cta_text}

Return the complete description.
"""
        
        description = self.client.generate_text(prompt).strip()
        
        # Ensure max length
        if len(description) > max_length:
            description = description[:max_length-3] + "..."
        
        logger.info(f"Generated description ({len(description)} chars)")
        return description
    
    def generate_tags(
        self,
        content_description: str,
        title: str,
        max_tags: int = 15
    ) -> List[str]:
        """Generate relevant tags/hashtags.
        
        Args:
            content_description: Description of video content
            title: Video title
            max_tags: Maximum number of tags
            
        Returns:
            List of tags
        """
        logger.info(f"Generating up to {max_tags} tags")
        
        prompt = f"""
Generate relevant tags for this YouTube Short:

Title: {title}
Content: {content_description}

Requirements:
- Generate {max_tags} relevant tags/hashtags
- Mix broad and specific tags
- Include trending keywords
- Optimize for YouTube search
- Use proper hashtag format (#tag)

Return as a JSON array of strings: ["#tag1", "#tag2", ...]
"""
        
        try:
            result = self.client.generate_json(prompt)
            
            if isinstance(result, dict) and 'tags' in result:
                tags = result['tags']
            elif isinstance(result, list):
                tags = result
            else:
                tags = []
            
            # Ensure hashtag format
            tags = [tag if tag.startswith('#') else f'#{tag}' for tag in tags]
            
            # Limit to max_tags
            tags = tags[:max_tags]
            
            logger.info(f"Generated {len(tags)} tags")
            return tags
        
        except Exception as e:
            logger.error(f"Failed to generate tags: {e}")
            # Return basic tags based on title
            words = title.lower().split()
            basic_tags = [f"#{word}" for word in words if len(word) > 3][:max_tags]
            return basic_tags
    
    def build_complete_metadata(
        self,
        content_description: str,
        category: str = "general",
        style: str = "engaging",
        platform: str = "youtube"
    ) -> Dict:
        """Build complete metadata package for a video.
        
        Args:
            content_description: Description of video content
            category: Video category
            style: Title style
            platform: Target platform (youtube, tiktok, instagram)
            
        Returns:
            Dictionary containing all metadata
        """
        logger.info(f"Building complete metadata for {platform}")
        
        # Platform-specific limits
        limits = {
            'youtube': {'title': 100, 'description': 5000, 'tags': 15},
            'tiktok': {'title': 150, 'description': 150, 'tags': 10},
            'instagram': {'title': 150, 'description': 2200, 'tags': 30}
        }
        
        platform_limits = limits.get(platform, limits['youtube'])
        
        # Generate title
        title = self.generate_title(
            content_description,
            max_length=platform_limits['title'],
            style=style
        )
        
        # Generate description
        description = self.generate_description(
            content_description,
            title,
            max_length=platform_limits['description'],
            include_cta=(platform == 'youtube')
        )
        
        # Generate tags
        tags = self.generate_tags(
            content_description,
            title,
            max_tags=platform_limits['tags']
        )
        
        metadata = {
            'title': title,
            'description': description,
            'tags': tags,
            'category': category,
            'platform': platform,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        logger.info("Complete metadata generated")
        return metadata
    
    def build_from_analysis(
        self,
        analysis_data: Dict,
        category: str = "general",
        style: str = "engaging",
        platform: str = "youtube"
    ) -> Dict:
        """Build metadata from video analysis data.
        
        Args:
            analysis_data: Video analysis dictionary
            category: Video category
            style: Title style
            platform: Target platform
            
        Returns:
            Dictionary containing all metadata
        """
        logger.info("Building metadata from analysis data")
        
        # Extract content description from analysis
        scenes = analysis_data.get('scenes', [])
        overall_style = analysis_data.get('overall_style', 'Unknown')
        overall_mood = analysis_data.get('overall_mood', 'Unknown')
        
        content_parts = [
            f"Style: {overall_style}",
            f"Mood: {overall_mood}",
            f"Scenes: {len(scenes)}"
        ]
        
        # Add scene descriptions
        for i, scene in enumerate(scenes[:3], 1):
            visual = scene.get('visual_description', 'N/A')
            content_parts.append(f"Scene {i}: {visual}")
        
        content_description = '\n'.join(content_parts)
        
        return self.build_complete_metadata(
            content_description,
            category=category,
            style=style,
            platform=platform
        )
    
    def optimize_for_seo(self, metadata: Dict, keywords: List[str]) -> Dict:
        """Optimize metadata for SEO with additional keywords.
        
        Args:
            metadata: Existing metadata dictionary
            keywords: Additional keywords to include
            
        Returns:
            Optimized metadata dictionary
        """
        logger.info(f"Optimizing metadata with {len(keywords)} keywords")
        
        optimized = metadata.copy()
        
        # Add keywords to description if not already present
        description = optimized['description']
        keywords_to_add = [kw for kw in keywords if kw.lower() not in description.lower()]
        
        if keywords_to_add:
            keywords_line = "\n\nKeywords: " + ", ".join(keywords_to_add)
            if len(description) + len(keywords_line) <= 5000:
                optimized['description'] = description + keywords_line
        
        # Add keywords as tags
        existing_tags = set(tag.lower().replace('#', '') for tag in optimized['tags'])
        new_tags = [f"#{kw}" for kw in keywords if kw.lower() not in existing_tags]
        optimized['tags'].extend(new_tags[:5])  # Add up to 5 new tags
        
        logger.info("Metadata optimized for SEO")
        return optimized
    
    def format_for_platform(self, metadata: Dict, target_platform: str) -> Dict:
        """Reformat metadata for a different platform.
        
        Args:
            metadata: Existing metadata dictionary
            target_platform: Target platform name
            
        Returns:
            Reformatted metadata
        """
        logger.info(f"Reformatting metadata for {target_platform}")
        
        # Get platform limits
        limits = {
            'youtube': {'title': 100, 'description': 5000, 'tags': 15},
            'tiktok': {'title': 150, 'description': 150, 'tags': 10},
            'instagram': {'title': 150, 'description': 2200, 'tags': 30}
        }
        
        platform_limits = limits.get(target_platform, limits['youtube'])
        
        formatted = metadata.copy()
        formatted['platform'] = target_platform
        
        # Truncate if needed
        if len(formatted['title']) > platform_limits['title']:
            formatted['title'] = formatted['title'][:platform_limits['title']-3] + "..."
        
        if len(formatted['description']) > platform_limits['description']:
            formatted['description'] = formatted['description'][:platform_limits['description']-3] + "..."
        
        formatted['tags'] = formatted['tags'][:platform_limits['tags']]
        
        logger.info(f"Metadata reformatted for {target_platform}")
        return formatted


def build_metadata(content_description: str, category: str = "general") -> Dict:
    """Convenience function to build metadata.
    
    Args:
        content_description: Description of video content
        category: Video category
        
    Returns:
        Metadata dictionary
    """
    builder = MetadataBuilder()
    return builder.build_complete_metadata(content_description, category)
