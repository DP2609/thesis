# client_page.py
import flet as ft
import os
import requests
import mimetypes

# API configuration
API_BASE_URL = "http://localhost:8000"  # Adjust this to your API server URL

class ClientPage(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="/client")
        self.page = page
        self.vertical_alignment = ft.MainAxisAlignment.START
        self.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

        # Lấy thông tin từ session
        self.username = self.page.session.get("username") or "Khách"
        self.token = self.page.session.get("token")

        # Tạo nút đăng xuất
        self.logout_button = ft.ElevatedButton("Đăng xuất", on_click=self.logout_clicked)

        # AppBar
        self.appbar = ft.AppBar(
            title=ft.Text("Phát hiện hình ảnh"),
            bgcolor=ft.Colors.AMBER,
            actions=[self.logout_button]
        )

        # File picker
        self.file_picker = ft.FilePicker(on_result=self.pick_files_result)
        self.page.overlay.append(self.file_picker)

        # Các thành phần UI
        self.title = ft.Text("Ứng dụng phát hiện hình ảnh", size=32, weight=ft.FontWeight.BOLD)
        self.subtitle = ft.Text(f"Chào mừng, {self.username}", size=16, color=ft.Colors.GREY_600)
        
        self.upload_button = ft.ElevatedButton(
            "Tải lên hình ảnh",
            icon=ft.Icons.UPLOAD_FILE,
            on_click=lambda _: self.file_picker.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.IMAGE
            )
        )
        
        self.img = ft.Image(
            src="",
            width=400,
            height=400,
            fit=ft.ImageFit.CONTAIN,
            visible=False
        )
        
        self.result_text = ft.Text("", size=16, selectable=True)
        
        # Tạo container có thể cuộn cho kết quả
        self.result_container = ft.Column(
            [
                ft.Container(
                    content=self.result_text,
                    padding=20,
                    border_radius=10,
                    bgcolor=ft.Colors.GREY_100,
                    width=400,
                    height=400,
                    alignment=ft.alignment.top_left
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            height=400
        )

        # Tạo layout chính
        self.controls = [
            ft.Column(
                [
                    ft.Row(
                        [
                            self.title,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    self.subtitle,
                    ft.Divider(),
                    self.upload_button,
                    ft.Row(
                        [
                            self.img,
                            self.result_container
                        ],
                        spacing=20,
                        alignment=ft.MainAxisAlignment.CENTER
                    )
                ],
                spacing=20,
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO
            )
        ]

    def get_auth_header(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def pick_files_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            selected_file = e.files[0]
            file_path = selected_file.path
            
            # Xử lý hình ảnh qua API
            try:
                # Hiển thị thông báo đang xử lý
                self.result_text.value = "Đang xử lý hình ảnh..."
                self.page.update()
                
                # Lấy phần mở rộng và loại nội dung
                file_extension = os.path.splitext(file_path)[1].lower()
                content_type = mimetypes.types_map.get(file_extension, 'application/octet-stream')
                
                # Gửi yêu cầu API với header xác thực và file
                with open(file_path, 'rb') as f:
                    files = {
                        'file': (
                            os.path.basename(file_path),
                            f,
                            content_type
                        )
                    }
                    headers = self.get_auth_header()
                    response = requests.post(
                        f"{API_BASE_URL}/detect",
                        files=files,
                        headers=headers
                    )
                
                if response.status_code == 200:
                    results = response.json()
                    self.result_text.value = results.get('response', 'Không nhận được phản hồi')
                else:
                    self.result_text.value = f"Lỗi: {response.status_code} - {response.text}"
                
                # Hiển thị hình ảnh
                self.img.src = file_path
                self.img.visible = True
                
            except requests.exceptions.RequestException as ex:
                self.result_text.value = f"Lỗi kết nối đến API: {str(ex)}"
            except Exception as ex:
                self.result_text.value = f"Lỗi xử lý hình ảnh: {str(ex)}"
            
            self.page.update()

    def logout_clicked(self, e):
        self.page.session.clear()
        # Thay vì chỉ chuyển hướng, hãy xóa tất cả views và thêm trang login
        self.page.views.clear()  # Xóa tất cả views hiện tại
        self.page.go("/login")   # Chuyển hướng đến trang login

if __name__ == "__main__":
    def main(page: ft.Page):
        page.title = "Test Client Page"
        page.session.set("username", "TestUserClient")
        page.session.set("token", "test_token")  # Thêm token giả để test
        client_view = ClientPage(page)
        page.views.append(client_view)
        page.update()
    ft.app(target=main)