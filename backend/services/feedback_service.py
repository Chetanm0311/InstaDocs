import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class FeedbackService:
    """Service for collecting and analyzing user feedback"""
    
    def __init__(self, storage_path: str = "./storage/feedback/feedback.json"):
        self.storage_path = Path(storage_path)
        
        # Ensure parent directory exists
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"📁 Feedback storage initialized at: {self.storage_path.absolute()}")
        except Exception as e:
            print(f"⚠️ Warning: Could not create feedback directory: {e}")
        
        self.feedback_data = self._load_feedback()
    
    def _load_feedback(self) -> List[dict]:
        """Load feedback from file"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"✅ Loaded {len(data)} feedback entries")
                    return data
            else:
                print("ℹ️ No existing feedback file, starting fresh")
                return []
        except json.JSONDecodeError as e:
            print(f"⚠️ Warning: Corrupted feedback file, starting fresh. Error: {e}")
            # Backup corrupted file
            if self.storage_path.exists():
                backup_path = self.storage_path.with_suffix('.json.backup')
                self.storage_path.rename(backup_path)
                print(f"📦 Backed up corrupted file to: {backup_path}")
            return []
        except Exception as e:
            print(f"❌ Error loading feedback: {e}")
            return []
    
    def _save_feedback(self) -> bool:
        """Save feedback to file"""
        try:
            # Write to temporary file first
            temp_path = self.storage_path.with_suffix('.tmp')
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Replace original file with temp file (atomic operation)
            temp_path.replace(self.storage_path)
            
            print(f"✅ Feedback saved successfully ({len(self.feedback_data)} entries)")
            return True
            
        except Exception as e:
            print(f"❌ Error saving feedback: {e}")
            print(f"   Storage path: {self.storage_path.absolute()}")
            print(f"   Directory exists: {self.storage_path.parent.exists()}")
            print(f"   Directory writable: {os.access(self.storage_path.parent, os.W_OK)}")
            return False
    
    def store_feedback(
        self, 
        query_id: str, 
        rating: int, 
        feedback_text: Optional[str] = None, 
        query: Optional[str] = None, 
        answer: Optional[str] = None, 
        confidence: Optional[float] = None
    ) -> dict:
        """
        Store user feedback
        
        Args:
            query_id: Unique identifier for the query
            rating: Rating from 1-5
            feedback_text: Optional text feedback
            query: The original question
            answer: The generated answer
            confidence: Confidence score of the answer
            
        Returns:
            The stored feedback entry
        """
        try:
            # Validate rating
            if not isinstance(rating, int) or rating < 1 or rating > 5:
                raise ValueError(f"Rating must be an integer between 1 and 5, got: {rating}")
            
            feedback_entry = {
                "feedback_id": len(self.feedback_data) + 1,
                "query_id": query_id,
                "rating": rating,
                "feedback_text": feedback_text,
                "query": query,
                "answer": answer,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"📝 Storing feedback: Rating={rating}, Query ID={query_id}")
            
            # Add to data
            self.feedback_data.append(feedback_entry)
            
            # Save immediately
            if self._save_feedback():
                print(f"✅ Feedback #{feedback_entry['feedback_id']} stored successfully")
                return feedback_entry
            else:
                # Rollback if save failed
                self.feedback_data.pop()
                raise Exception("Failed to save feedback to file")
                
        except Exception as e:
            print(f"❌ Error storing feedback: {e}")
            raise
    
    def get_all_feedback(self) -> List[dict]:
        """Get all feedback entries"""
        return self.feedback_data
    
    def get_recent_feedback(self, limit: int = 10) -> List[dict]:
        """Get most recent feedback entries"""
        return sorted(
            self.feedback_data, 
            key=lambda x: x.get('timestamp', ''), 
            reverse=True
        )[:limit]
    
    def get_feedback_stats(self) -> Dict:
        """Get statistics about feedback"""
        if not self.feedback_data:
            return {
                "total_feedback": 0,
                "average_rating": 0,
                "rating_distribution": {str(i): 0 for i in range(1, 6)},
                "low_rated_count": 0,
                "suggestions": []
            }
        
        ratings = [f["rating"] for f in self.feedback_data]
        avg_rating = sum(ratings) / len(ratings)
        
        # Rating distribution
        rating_dist = {str(i): ratings.count(i) for i in range(1, 6)}
        
        # Analyze low-rated queries
        low_rated = [f for f in self.feedback_data if f["rating"] <= 2]
        
        return {
            "total_feedback": len(self.feedback_data),
            "average_rating": round(avg_rating, 2),
            "rating_distribution": rating_dist,
            "low_rated_count": len(low_rated),
            "high_rated_count": sum(1 for f in self.feedback_data if f["rating"] >= 4),
            "suggestions": self._generate_suggestions(low_rated)
        }
    
    def _generate_suggestions(self, low_rated: List[dict]) -> List[str]:
        """Generate improvement suggestions based on low ratings"""
        suggestions = []
        
        if len(low_rated) > 0:
            # Calculate average confidence for low-rated answers
            confidences = [f.get("confidence", 0.5) for f in low_rated if f.get("confidence") is not None]
            
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                
                if avg_confidence < 0.4:
                    suggestions.append(
                        "Low confidence detected in poor answers - upload more relevant documents"
                    )
                elif avg_confidence > 0.7:
                    suggestions.append(
                        "High confidence but low ratings - consider improving LLM prompts or using a better model"
                    )
            
            if len(low_rated) > 3:
                suggestions.append(
                    f"Multiple low-rated answers ({len(low_rated)}) - review knowledge base coverage"
                )
            
            # Check for specific patterns
            low_rated_queries = [f.get("query", "").lower() for f in low_rated if f.get("query")]
            if low_rated_queries:
                # Find common words in low-rated queries
                from collections import Counter
                words = []
                for query in low_rated_queries:
                    words.extend(query.split())
                
                common_words = Counter(words).most_common(3)
                if common_words:
                    topics = [word for word, count in common_words if count > 1 and len(word) > 3]
                    if topics:
                        suggestions.append(
                            f"Common topics in low-rated queries: {', '.join(topics)} - consider adding documents on these topics"
                        )
        
        return suggestions if suggestions else ["System is performing well - keep the knowledge base updated"]
    
    def get_feedback_by_query_id(self, query_id: str) -> Optional[dict]:
        """Get feedback for a specific query"""
        for feedback in self.feedback_data:
            if feedback.get("query_id") == query_id:
                return feedback
        return None
    
    def delete_feedback(self, feedback_id: int) -> bool:
        """Delete a specific feedback entry"""
        try:
            initial_length = len(self.feedback_data)
            self.feedback_data = [f for f in self.feedback_data if f.get("feedback_id") != feedback_id]
            
            if len(self.feedback_data) < initial_length:
                self._save_feedback()
                print(f"🗑️ Deleted feedback #{feedback_id}")
                return True
            else:
                print(f"⚠️ Feedback #{feedback_id} not found")
                return False
        except Exception as e:
            print(f"❌ Error deleting feedback: {e}")
            return False
    
    def export_feedback_csv(self, output_path: str = "./storage/feedback/feedback_export.csv") -> bool:
        """Export feedback to CSV file"""
        try:
            import csv
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if self.feedback_data:
                    fieldnames = list(self.feedback_data[0].keys())
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.feedback_data)
            
            print(f"📊 Exported {len(self.feedback_data)} feedback entries to: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error exporting feedback: {e}")
            return False
