# login_page.py
import flet as ft
import requests

# API configuration
API_BASE_URL = "http://localhost:8000"  # Adjust this to your API server URL

class Auth:
    def __init__(self):
        self.token = None
        self.username = None
        self.is_admin = False

    def login(self, username: str, password: str) -> bool:
        try:
            response = requests.post(
                f"{API_BASE_URL}/token",
                data={
                    "username": username,
                    "password": password
                }
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.username = data.get("user", {}).get("username")
                self.is_admin = data.get("user", {}).get("is_admin", False)
                return True
            return False
        except requests.exceptions.RequestException:
            return False

    def is_authenticated(self) -> bool:
        return self.token is not None

    def register(self, username: str, password: str ,email : str) -> bool:
        try:
            response = requests.post(
                f"{API_BASE_URL}/register",
                json={
                    "username": username,
                    "password": password,
                    "email": email,  # Assuming username is used as email for simplicity
                }
            )
            return response.status_code == 201
        except requests.exceptions.RequestException:
            return False

class LoginPage(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="/login")  # Gọi constructor của ft.View và đặt route
        self.page = page  # Lưu lại page để có thể truy cập page.go, page.session
        self.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        # Initialize auth
        self.auth = Auth()

        self.username_field = ft.TextField(label="Tên đăng nhập", width=300, autofocus=True)
        self.password_field = ft.TextField(label="Mật khẩu", password=True, can_reveal_password=True, width=300, on_submit=self.login_clicked)
        self.error_text = ft.Text(value="", color=ft.Colors.RED)
        self.login_button = ft.ElevatedButton(text="Đăng nhập", on_click=self.login_clicked, width=300, height=40)
         # Auto-fill test account button (optional)
        self.register_button = ft.ElevatedButton(
            text="Đăng kí tài khoản",
            on_click=lambda e: self.page.go("/register"), 
            width=300
        )
        # Auto-fill test account button (optional)
        self.auto_fill_button = ft.ElevatedButton(
            text="Điền tài khoản test", 
            on_click=self.auto_fill_test_account, 
            width=300
        )

        self.controls = [
            ft.Column(
                [
                    ft.Text("Đăng nhập", size=30, weight=ft.FontWeight.BOLD),
                    self.username_field,
                    self.password_field,
                    self.login_button,
                    self.register_button,
                    self.auto_fill_button,
                    self.error_text,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
                width=400,  # Giới hạn chiều rộng của cột
            )
        ]

    def auto_fill_test_account(self, e):
        self.username_field.value = "andrews"
        self.password_field.value = "Andrews@123"
        self.page.update()

    def login_clicked(self, e):
        username = self.username_field.value
        password = self.password_field.value

        if not username or not password:
            self.error_text.value = "Vui lòng nhập tên đăng nhập và mật khẩu."
            self.page.update()
            return

        try:
            if self.auth.login(username, password):
                # Store auth info in session
                self.page.session.set("user_role", "admin" if self.auth.is_admin else "user")
                self.page.session.set("username", self.auth.username)
                self.page.session.set("token", self.auth.token)
                
                # Navigate based on role
                if self.auth.is_admin:
                    self.page.go("/admin")
                else:
                    self.page.go("/client")
                self.error_text.value = ""
            else:
                self.error_text.value = "Tên đăng nhập hoặc mật khẩu không đúng."
        except Exception as ex:
            self.error_text.value = f"Lỗi đăng nhập: {str(ex)}"
        
        self.page.update()

if __name__ == "__main__":
    # Phần này chỉ để kiểm tra riêng trang login
    def main(page: ft.Page):
        page.title = "Test Login Page"
        # Khi tạo instance của class kế thừa từ ft.View, nó chính là View
        login_view = LoginPage(page)
        page.views.append(login_view)  # Thêm view vào danh sách views của page
        page.update()
    ft.app(target=main)