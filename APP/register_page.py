import time
import flet as ft
import requests

# API configuration
API_BASE_URL = "http://localhost:8000"  # Adjust this to your API server URL

class RegisterPage(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="/register")  # Call ft.View constructor and set route
        self.page = page
        self.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        # Initialize form fields
        self.email_field = ft.TextField(
            label="Email",
            width=300,
            autofocus=True
        )
        
        self.username_field = ft.TextField(
            label="Tên đăng nhập",
            width=300
        )
        
        self.password_field = ft.TextField(
            label="Mật khẩu",
            width=300,
            password=True,
            can_reveal_password=True
        )
        
        self.confirm_password_field = ft.TextField(
            label="Xác nhận mật khẩu",
            width=300,
            password=True,
            can_reveal_password=True
        )

        self.error_text = ft.Text(value="", color=ft.Colors.RED)
        self.success_text = ft.Text(value="", color=ft.Colors.GREEN)

        # Buttons
        self.register_button = ft.ElevatedButton(
            text="Đăng ký",
            on_click=self.register_clicked,
            width=300,
            height=40
        )

        self.login_button = ft.ElevatedButton(
            text="Đã có tài khoản? Đăng nhập",
            on_click=lambda e: self.page.go("/login"),
            width=300
        )

        # Layout
        self.controls = [
            ft.Column(
                [
                    ft.Text("Đăng ký tài khoản", size=30, weight=ft.FontWeight.BOLD),
                    self.email_field,
                    self.username_field,
                    self.password_field,
                    self.confirm_password_field,
                    self.register_button,
                    self.login_button,
                    self.error_text,
                    self.success_text,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
                width=400,  # Limit column width
            )
        ]

    def validate_form(self):
        if not all([
            self.email_field.value,
            self.username_field.value,
            self.password_field.value,
            self.confirm_password_field.value
        ]):
            self.error_text.value = "Vui lòng điền đầy đủ thông tin."
            return False

        if "@" not in self.email_field.value or "." not in self.email_field.value:
            self.error_text.value = "Email không hợp lệ."
            return False

        if len(self.username_field.value) < 3:
            self.error_text.value = "Tên đăng nhập phải có ít nhất 3 ký tự."
            return False

        if len(self.password_field.value) < 8:
            self.error_text.value = "Mật khẩu phải có ít nhất 8 ký tự."
            return False

        if self.password_field.value != self.confirm_password_field.value:
            self.error_text.value = "Mật khẩu xác nhận không khớp."
            return False

        self.error_text.value = ""
        return True

    def register_clicked(self, e):
        if not self.validate_form():
            self.page.update()
            return

        try:
            response = requests.post(
                f"{API_BASE_URL}/register",
                json={
                    "email": self.email_field.value,
                    "username": self.username_field.value,
                    "password": self.password_field.value,
                }
            )
            
            print(response.status_code)
            
            if response.status_code == 200 or response.status_code == 201:
                self.success_text.value = "Đăng ký thành công! Vui lòng đăng nhập."
                self.error_text.value = ""
                self.page.update()
                # Redirect to login page after a short delay
                time.sleep(2)
                self.page.go("/login")
            else:
                self.error_text.value = "Đăng ký thất bại. Tên đăng nhập hoặc email đã tồn tại."
        except Exception as ex:
            self.error_text.value = f"Lỗi đăng ký: {str(ex)}"
        self.page.update()

if __name__ == "__main__":
    # For testing the register page independently
    def main(page: ft.Page):
        page.title = "Test Register Page"
        register_view = RegisterPage(page)
        page.views.append(register_view)
        page.update()
    ft.app(target=main)