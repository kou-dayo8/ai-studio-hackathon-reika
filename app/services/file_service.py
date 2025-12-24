import os
import uuid
import imghdr
from config import Config

class FileService:
    def __init__(self):
        self.upload_path = os.path.join('frontend', 'assets', 'images', 'reviews')
        # ディレクトリが存在しない場合は作成
        os.makedirs(self.upload_path, exist_ok=True)

    def validate_image(self, file):
        """
        [Level 5-B 修正箇所]
        ファイルの拡張子だけでなく、中身（マジックナンバー）をチェックするぜ！
        """
        if not file:
            return 'ファイルがありません'

        # 1. まずファイルの中身を少し読み取って、実際の形式を判定
        # (マジックナンバーによる判定)
        file_data = file.read(2048)  # 先頭部分を読み取る
        file_type = imghdr.what(None, file_data)
        
        # ファイルポインタを先頭に戻す（これを忘れると後で保存するときに空になるぜ！）
        file.seek(0)

        # 2. 許可された画像形式かチェック
        allowed_types = ['jpeg', 'png', 'gif']
        if file_type not in allowed_types:
            return '画像ファイルではありません（不正な形式です）'

        # 3. 拡張子もチェック（多層防御だぜ！）
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in Config.ALLOWED_EXTENSIONS:
            return 'jpg, jpeg, png, gifのみ対応しています'

        return None

    def save_review_photo(self, file, review_id):
        """
        レビュー画像をバリデーションして保存するぜ。
        """
        try:
            # バリデーションを実行
            error = self.validate_image(file)
            if error:
                # 実際の開発ではここで例外を投げたり、エラーを返したりする
                print(f"Validation Error: {error}")
                raise Exception(error)

            # 保存用のファイル名を生成
            file_ext = os.path.splitext(file.filename)[1].lower()
            filename = f'review_{review_id}_{uuid.uuid4().hex[:8]}{file_ext}'
            save_path = os.path.join(self.upload_path, filename)

            # ファイルを保存
            file.save(save_path)
            return filename

        except Exception as e:
            print(f"Error saving photo: {e}")
            raise e

    def delete_review_photo(self, filename):
        """画像を削除するぜ"""
        if not filename:
            return
        
        file_path = os.path.join(self.upload_path, filename)
        if os.path.exists(file_path):
            os.remove(file_path)