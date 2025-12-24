"""
統計データのビジネスロジックを担当
"""
import time
from repositories.stats_repository import StatsRepository

class StatsService:
    """統計データのビジネスロジック"""

    def __init__(self):
        self.repository = StatsRepository()
        # [Level 5-F 修正] キャッシュ保存用と有効期限（300秒）を設定するぜ！
        self.cache = {}
        self.cache_timeout = 300

    def get_summary(self):
        """基本統計情報を取得（キャッシュ機能付きだぜ！）"""
        now = time.time()
        
        # 1. キャッシュをチェックするぜ
        if 'summary' in self.cache:
            cached_data, cached_time = self.cache['summary']
            if now - cached_time < self.cache_timeout:
                # 期限内なら、そのままメモしたデータを返すぜ！
                return cached_data

        # 2. キャッシュがない、または期限切れならデータベースから取得
        summary = self.repository.fetch_summary()
        
        if not summary:
            return {
                'total_spots': 0,
                'total_reviews': 0,
                'total_users': 0,
                'total_events': 0,
                'avg_rating_overall': 0
            }

        # [おまけ修正] NULLチェックを安全に行うぜ！
        rating = summary.get('avg_rating_overall')
        summary['avg_rating_overall'] = round(rating, 1) if rating is not None else 0

        # 3. 取得した結果をキャッシュに保存するぜ
        self.cache['summary'] = (summary, now)
        
        return summary

    def get_spots_by_area(self, area_filter=None):
        """地域別観光地数を取得"""
        areas = self.repository.fetch_spots_by_area(area_filter)
        return areas if areas else []

    def get_events_by_month(self):
        """月別イベント数を取得"""
        months = self.repository.fetch_events_by_month()
        result = []
        month_dict = {month['month']: month['count'] for month in months}

        # 月名は日本語にするのが群馬スタイルだぜ！
        for month_num in range(1, 13):
            result.append({
                'month': month_num,
                'month_name': f"{month_num}月",
                'count': month_dict.get(month_num, 0)
            })
        return result

    def get_top_spots(self, limit=5):
        """人気観光地ランキングを取得"""
        try:
            limit = int(limit)
            limit = max(1, min(limit, 20))
        except (ValueError, TypeError):
            limit = 5

        spots = self.repository.fetch_top_spots(limit)
        if not spots:
            return []

        for spot in spots:
            rating = spot.get('avg_rating')
            spot['avg_rating'] = round(rating, 1) if rating is not None else 0
        return spots