"""Prompt generator for video generation from scene analysis."""

import json
from typing import Dict, List, Optional
from pathlib import Path

from .gemini_client import GeminiClient
from ..utils.logger import get_analysis_logger
from ..utils.exceptions import AnalysisError

logger = get_analysis_logger(__name__)


class PromptGenerator:
    """Generate video generation prompts from scene analysis."""
    
    def __init__(self):
        """Initialize prompt generator with Gemini client."""
        self.client = GeminiClient()
        logger.info("Prompt generator initialized")
    
    def generate_prompts_from_scenes(
        self,
        scene_analysis: Dict,
        style: str = "realistic"
    ) -> Dict:
        """Generate video generation prompts from scene analysis.
        
        Args:
            scene_analysis: Scene analysis dictionary
            style: Desired video style (realistic, animated, artistic, cinematic)
            
        Returns:
            Dictionary containing generation prompts for each scene
            
        Raises:
            AnalysisError: If prompt generation fails
        """
        logger.info(f"Generating prompts for {len(scene_analysis.get('scenes', []))} scenes with style: {style}")
        
        try:
            # Convert scene analysis to formatted string
            scene_data = json.dumps(scene_analysis, indent=2)
            
            # Generate prompts using Gemini
            result = self.client.analyze_json_with_template(
                'prompt_generation',
                scene_data=scene_data,
                style=style
            )
            
            # Validate result
            self._validate_prompts(result)
            
            logger.info(f"Generated {len(result.get('scene_prompts', []))} scene prompts")
            return result
        
        except Exception as e:
            logger.error(f"Failed to generate prompts: {e}")
            raise AnalysisError(f"Prompt generation failed: {e}")
    
    def _validate_prompts(self, result: Dict) -> None:
        """Validate prompt generation result.
        
        Args:
            result: Prompt generation result
            
        Raises:
            AnalysisError: If validation fails
        """
        if 'scene_prompts' not in result:
            raise AnalysisError("Missing 'scene_prompts' in result")
        
        scene_prompts = result['scene_prompts']
        if not isinstance(scene_prompts, list):
            raise AnalysisError("'scene_prompts' must be a list")
        
        if not scene_prompts:
            raise AnalysisError("No scene prompts generated")
    
    def enhance_prompt(
        self,
        base_prompt: str,
        style: str = "realistic",
        quality_terms: Optional[List[str]] = None
    ) -> str:
        """Enhance a base prompt with style and quality terms.
        
        Args:
            base_prompt: Base prompt text
            style: Video style
            quality_terms: Optional list of quality enhancement terms
            
        Returns:
            Enhanced prompt string
        """
        enhanced_parts = [base_prompt]
        
        # Add style keywords
        style_keywords = {
            'realistic': ['photorealistic', 'natural lighting', 'real-world'],
            'animated': ['animated style', 'vibrant colors', '3D rendered'],
            'artistic': ['artistic', 'painterly', 'stylized'],
            'cinematic': ['cinematic', 'dramatic lighting', 'film quality']
        }
        
        if style in style_keywords:
            enhanced_parts.extend(style_keywords[style])
        
        # Add quality terms
        if quality_terms:
            enhanced_parts.extend(quality_terms)
        else:
            # Default quality terms
            enhanced_parts.extend([
                'high quality',
                'detailed',
                'sharp focus',
                '4K quality'
            ])
        
        enhanced_prompt = ', '.join(enhanced_parts)
        logger.debug(f"Enhanced prompt: {enhanced_prompt[:100]}...")
        
        return enhanced_prompt
    
    def generate_metadata(
        self,
        scene_analysis: Dict,
        target_audience: str = "general"
    ) -> Dict:
        """Generate video metadata (title, description, tags).
        
        Args:
            scene_analysis: Scene analysis dictionary
            target_audience: Target audience description
            
        Returns:
            Dictionary containing metadata
            
        Raises:
            AnalysisError: If metadata generation fails
        """
        logger.info("Generating video metadata")
        
        try:
            # Extract content description from scenes
            scenes = scene_analysis.get('scenes', [])
            overall_style = scene_analysis.get('overall_style', 'Unknown')
            overall_mood = scene_analysis.get('overall_mood', 'Unknown')
            
            content_description = f"""
Video Style: {overall_style}
Mood: {overall_mood}
Scene Count: {len(scenes)}
Target Audience: {target_audience}

Scenes Overview:
"""
            
            for i, scene in enumerate(scenes[:5], 1):  # First 5 scenes
                content_description += f"\n{i}. {scene.get('visual_description', 'N/A')}"
            
            # Generate metadata using Gemini
            result = self.client.analyze_json_with_template(
                'metadata_generation',
                content_description=content_description
            )
            
            # Validate result
            required_fields = ['title', 'description', 'tags']
            for field in required_fields:
                if field not in result:
                    raise AnalysisError(f"Missing required field in metadata: {field}")
            
            logger.info(f"Generated metadata: title='{result['title'][:50]}...', {len(result['tags'])} tags")
            return result
        
        except Exception as e:
            logger.error(f"Failed to generate metadata: {e}")
            raise AnalysisError(f"Metadata generation failed: {e}")
    
    def create_full_generation_plan(
        self,
        scene_analysis: Dict,
        style: str = "realistic",
        target_audience: str = "general"
    ) -> Dict:
        """Create a complete video generation plan.
        
        Args:
            scene_analysis: Scene analysis dictionary
            style: Video style
            target_audience: Target audience
            
        Returns:
            Complete generation plan dictionary
        """
        logger.info("Creating full video generation plan")
        
        # Generate scene prompts
        prompts = self.generate_prompts_from_scenes(scene_analysis, style)
        
        # Generate metadata
        metadata = self.generate_metadata(scene_analysis, target_audience)
        
        # Combine into full plan
        generation_plan = {
            'style': style,
            'target_audience': target_audience,
            'scene_analysis': scene_analysis,
            'scene_prompts': prompts.get('scene_prompts', []),
            'metadata': metadata,
            'total_scenes': len(scene_analysis.get('scenes', [])),
            'estimated_duration': scene_analysis.get('total_duration', 60)
        }
        
        logger.info("Full generation plan created")
        return generation_plan
    
    def save_generation_plan(
        self,
        generation_plan: Dict,
        output_dir: str = "data/analysis"
    ) -> Path:
        """Save generation plan to a JSON file.
        
        Args:
            generation_plan: Generation plan dictionary
            output_dir: Output directory path
            
        Returns:
            Path to saved file
        """
        from datetime import datetime
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        video_id = generation_plan.get('scene_analysis', {}).get('video_id', 'unknown')
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"generation_plan_{video_id}_{timestamp}.json"
        
        file_path = output_path / filename
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(generation_plan, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Generation plan saved to: {file_path}")
        return file_path
    
    def generate_simple_prompts(
        self,
        scenes: List[Dict],
        style: str = "realistic"
    ) -> List[str]:
        """Generate simple text prompts from scenes (without Gemini).
        
        Args:
            scenes: List of scene dictionaries
            style: Video style
            
        Returns:
            List of prompt strings
        """
        logger.info(f"Generating simple prompts for {len(scenes)} scenes")
        
        prompts = []
        
        for scene in scenes:
            visual_desc = scene.get('visual_description', '')
            action = scene.get('action', '')
            camera = scene.get('camera', '')
            lighting = scene.get('lighting', '')
            mood = scene.get('mood', '')
            
            # Build prompt from scene components
            prompt_parts = []
            
            if visual_desc:
                prompt_parts.append(visual_desc)
            
            if action:
                prompt_parts.append(f"Action: {action}")
            
            if camera:
                prompt_parts.append(f"Camera: {camera}")
            
            if lighting:
                prompt_parts.append(f"Lighting: {lighting}")
            
            if mood:
                prompt_parts.append(f"Mood: {mood}")
            
            base_prompt = '. '.join(prompt_parts)
            
            # Enhance prompt
            enhanced = self.enhance_prompt(base_prompt, style)
            
            prompts.append(enhanced)
        
        logger.info(f"Generated {len(prompts)} simple prompts")
        return prompts
