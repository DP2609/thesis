import flet as ft
import os
import sys
import requests
import json
from PIL import Image
import io
import base64
import mimetypes

# API configuration
API_BASE_URL = "http://localhost:8000"  # Adjust this to your API server URL

class Auth:
    def __init__(self):
        self.token = None
        self.username = None

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
                self.username = username
                return True
            return False
        except requests.exceptions.RequestException:
            return False

    def register(self, username: str, password: str) -> bool:
        try:
            response = requests.post(
                f"{API_BASE_URL}/register",
                json={
                    "username": username,
                    "password": password
                }
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def is_authenticated(self) -> bool:
        return self.token is not None

    def get_auth_header(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

def main(page: ft.Page):
    # Configure the page
    page.title = "Image Detection App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window_width = 800
    page.window_height = 600
    page.window_resizable = True

    # Initialize auth
    auth = Auth()

    # Login page components
    login_username = ft.TextField(label="Username", width=300)
    login_password = ft.TextField(label="Password", password=True, width=300)
    login_error = ft.Text("", color=ft.colors.RED)
    
    # Register page components
    register_username = ft.TextField(label="Username", width=300)
    register_password = ft.TextField(label="Password", password=True, width=300)
    register_confirm_password = ft.TextField(label="Confirm Password", password=True, width=300)
    register_error = ft.Text("", color=ft.colors.RED)

    def login_click(e):
        if auth.login(login_username.value, login_password.value):
            page.go("/detection")
        else:
            login_error.value = "Invalid username or password"
            page.update()

    def register_click(e):
        if register_password.value != register_confirm_password.value:
            register_error.value = "Passwords do not match"
        else:
            if auth.register(register_username.value, register_password.value):
                page.go("/login")
            else:
                register_error.value = "Registration failed"
        page.update()

    def logout_click(e):
        auth.token = None
        auth.username = None
        page.go("/login")

    # Login page
    login_page = ft.View(
        "/login",
        [
            ft.Column(
                [
                    ft.Text("Login", size=32, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    login_username,
                    login_password,
                    login_error,
                    ft.ElevatedButton("Login", on_click=login_click),
                    ft.TextButton("Don't have an account? Register", on_click=lambda _: page.go("/register"))
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.CENTER
    )

    # Register page
    register_page = ft.View(
        "/register",
        [
            ft.Column(
                [
                    ft.Text("Register", size=32, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    register_username,
                    register_password,
                    register_confirm_password,
                    register_error,
                    ft.ElevatedButton("Register", on_click=register_click),
                    ft.TextButton("Already have an account? Login", on_click=lambda _: page.go("/login"))
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.CENTER
    )

    # Detection page components
    def pick_files_result(e: ft.FilePickerResultEvent):
        if e.files:
            selected_file = e.files[0]
            file_path = selected_file.path
            
            # Process the image through API
            try:
                # Show loading indicator
                result_text.value = "Processing image..."
                page.update()
                
                # Get file extension and content type
                file_extension = os.path.splitext(file_path)[1].lower()
                content_type = mimetypes.types_map.get(file_extension, 'application/octet-stream')
                
                # Make API request with auth header and file
                with open(file_path, 'rb') as f:
                    files = {
                        'file': (
                            os.path.basename(file_path),
                            f,
                            content_type
                        )
                    }
                    headers = auth.get_auth_header()
                    response = requests.post(
                        f"{API_BASE_URL}/detect",
                        files=files,
                        headers=headers
                    )
                
                if response.status_code == 200:
                    results = response.json()
                    
                    # Display results
                    result_text.value = results.get('response', 'No response received')
                
                else:
                    result_text.value = f"Error: {response.status_code} - {response.text}"
                
                # Display the image
                img.src = file_path
                img.visible = True
                
            except requests.exceptions.RequestException as ex:
                result_text.value = f"Error connecting to API: {str(ex)}"
            except Exception as ex:
                result_text.value = f"Error processing image: {str(ex)}"
            
            page.update()

    # File picker
    file_picker = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(file_picker)

    # Detection page UI Components
    title = ft.Text("Image Detection App", size=32, weight=ft.FontWeight.BOLD)
    subtitle = ft.Text(f"Welcome, {auth.username}", size=16, color=ft.colors.GREY_600)
    
    upload_button = ft.ElevatedButton(
        "Upload Image",
        icon=ft.icons.UPLOAD_FILE,
        on_click=lambda _: file_picker.pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.IMAGE
        )
    )
    
    img = ft.Image(
        src="",
        width=400,
        height=400,
        fit=ft.ImageFit.CONTAIN,
        visible=False
    )
    
    result_text = ft.Text("", size=16, selectable=True)
    
    # Create a scrollable container for the results
    result_container = ft.Column(
        [
            ft.Container(
                content=result_text,
                padding=20,
                border_radius=10,
                bgcolor=ft.colors.GREY_100,
                width=400,
                height=400,
                alignment=ft.alignment.top_left
            )
        ],
        scroll=ft.ScrollMode.AUTO,
        height=400
    )
    
    # Detection page
    detection_page = ft.View(
        "/detection",
        [
            ft.Column(
                [
                    ft.Row(
                        [
                            title,
                            ft.ElevatedButton("Logout", on_click=logout_click)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    subtitle,
                    ft.Divider(),
                    upload_button,
                    ft.Row(
                        [
                            img,
                            result_container
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
        ],
        scroll=ft.ScrollMode.AUTO
    )

    def route_change(e):
        page.views.clear()
        if not auth.is_authenticated() and e.route != "/register":
            page.views.append(login_page)
        elif e.route == "/register":
            page.views.append(register_page)
        else:
            page.views.append(detection_page)
        page.update()

    def view_pop(e):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # Start with login page
    page.go("/login")

if __name__ == "__main__":
    ft.app(target=main) 