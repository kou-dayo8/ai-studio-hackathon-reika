"""
レビューのビジネスロジック
"""
from repositories.review_repository import ReviewRepository
from services.file_service import FileService

class ReviewService:
    """レビューに関するビジネスロジック"""

    def __init__(self):
        self.review_repo = ReviewRepository()
        self.file_service = FileService()

    def get_reviews_by_spot(self, spot_id):
        """観光地のレビューを取得"""
        # N+1クエリ問題（Level 5-Dとかで修正が必要になる箇所だぜ）
        from repositories.user_repository import UserRepository
        user_repo = UserRepository()

        reviews = self.review_repo.find_by_spot_id(spot_id)

        # 各レビューにユーザー名を追加
        for review in reviews:
            user = user_repo.find_by_id(review['user_id'])
            review['user_name'] = user['name'] if user else '不明'

        return reviews

    def create_review(self, review_data):
        """レビューを作成（画像なし）"""
        # 必須フィールドチェック
        required_fields = ['user_id', 'spot_id', 'review_content', 'rating']
        for field in required_fields:
            if field not in review_data:
                return {'success': False, 'error': f'{field}が指定されていません'}

        # 重複チェック
        existing_review = self.review_repo.find_by_user_and_spot(
            review_data['user_id'],
            review_data['spot_id']
        )
        if existing_review:
            return {
                'success': False,
                'error': 'この観光地には既にレビューを投稿済みです。1つの観光地につき1つのレビューのみ投稿できます。'
            }

        # レビュー作成
        review_id = self.review_repo.create(review_data)

        if review_id:
            return {
                'success': True,
                'review_id': review_id,
                'message': 'レビューを投稿しました'
            }
        else:
            return {'success': False, 'error': 'レビューの作成に失敗しました'}

    def create_review_with_photo(self, request):
        """
        [Level 5-A 修正済] レビューを作成（画像あり）
        画像保存に失敗した場合は、データベースのレビューを削除（ロールバック）して不整合を防ぐぜ！
        """
        # フォームデータの取得
        user_id = request.form.get('user_id')
        spot_id = request.form.get('spot_id')
        review_content = request.form.get('review_content')
        rating = request.form.get('rating')
        photo = request.files.get('photo')

        # 必須フィールドチェック
        if not all([user_id, spot_id, review_content, rating]):
            return {'success': False, 'error': '必須項目が不足しています'}

        # 重複チェック
        existing_review = self.review_repo.find_by_user_and_spot(user_id, spot_id)
        if existing_review:
            return {
                'success': False,
                'error': 'この観光地には既にレビューを投稿済みです。1つの観光地につき1つのレビューのみ投稿できます。'
            }

        # 画像のバリデーション
        if photo and photo.filename:
            validation_error = self.file_service.validate_image(photo)
            if validation_error:
                return {'success': False, 'error': validation_error}

        # レビュー作成
        review_data = {
            'user_id': user_id,
            'spot_id': spot_id,
            'review_content': review_content,
            'rating': rating
        }
        review_id = self.review_repo.create(review_data)

        if not review_id:
            return {'success': False, 'error': 'レビューの作成に失敗しました'}

        # 画像保存
        photo_filename = None
        if photo and photo.filename:
            try:
                # 画像を保存してDBを更新
                photo_filename = self.file_service.save_review_photo(photo, review_id)
                self.review_repo.update_photo_filename(review_id, photo_filename)
            except Exception as e:
                # [Level 5-A 修正箇所] 画像保存に失敗したら、作成したレビューを削除（ロールバック）する
                self.review_repo.delete(review_id)
                print(f"画像保存エラーによりロールバックしました: {e}")
                return {
                    'success': False, 
                    'error': '画像の保存に失敗したため、レビューの投稿を中止しました。'
                }

        return {
            'success': True,
            'review_id': review_id,
            'photo_filename': photo_filename,
            'message': 'レビューを投稿しました'
        }

    def delete_review(self, review_id, user_id):
        """レビューを削除（権限チェック付き）"""
        review = self.review_repo.find_by_id(review_id)
        if not review:
            return {'success': False, 'error': 'レビューが見つかりません'}

        if self.review_repo.delete(review_id):
            return {
                'success': True,
                'message': 'レビューを削除しました'
            }
        else:
            return {'success': False, 'error': 'レビューの削除に失敗しました'}