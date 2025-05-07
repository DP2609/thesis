import flet as ft
import requests
import os
import sys
from datetime import datetime

# API configuration
API_BASE_URL = "http://localhost:8000"

class AdminPage:
    def __init__(self, page: ft.Page, auth_token: str):
        self.page = page
        self.auth_token = auth_token
        self.headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Initialize UI components
        self.initialize_ui()
        
    def initialize_ui(self):
        # Create tabs for different sections
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Users",
                    content=self.create_users_tab()
                ),
                ft.Tab(
                    text="Chat History",
                    content=self.create_chat_history_tab()
                )
            ],
            expand=1
        )
        
        # Add tabs to page
        self.page.add(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Admin Dashboard", size=32, weight=ft.FontWeight.BOLD),
                            ft.ElevatedButton("Logout", on_click=self.logout)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Divider(),
                    self.tabs
                ],
                expand=True
            )
        )
        
    def create_users_tab(self):
        # Users table
        self.users_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Username")),
                ft.DataColumn(ft.Text("Email")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Created At")),
                ft.DataColumn(ft.Text("Actions"))
            ],
            rows=[]
        )
        
        # Search and filter controls
        search_bar = ft.TextField(
            label="Search users",
            prefix_icon=ft.icons.SEARCH,
            on_change=self.search_users
        )
        
        # Pagination controls
        pagination = ft.Row(
            [
                ft.ElevatedButton("Previous", on_click=lambda _: self.change_page(-1)),
                ft.Text("Page 1"),
                ft.ElevatedButton("Next", on_click=lambda _: self.change_page(1))
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        return ft.Column(
            [
                search_bar,
                self.users_table,
                pagination
            ],
            scroll=ft.ScrollMode.AUTO
        )
        
    def create_chat_history_tab(self):
        # Chat history table
        self.chat_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("User")),
                ft.DataColumn(ft.Text("Message")),
                ft.DataColumn(ft.Text("Response")),
                ft.DataColumn(ft.Text("Date")),
                ft.DataColumn(ft.Text("Image"))
            ],
            rows=[]
        )
        
        # Search and filter controls
        search_bar = ft.TextField(
            label="Search chat history",
            prefix_icon=ft.icons.SEARCH,
            on_change=self.search_chat_history
        )
        
        # Pagination controls
        pagination = ft.Row(
            [
                ft.ElevatedButton("Previous", on_click=lambda _: self.change_chat_page(-1)),
                ft.Text("Page 1"),
                ft.ElevatedButton("Next", on_click=lambda _: self.change_chat_page(1))
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        return ft.Column(
            [
                search_bar,
                self.chat_table,
                pagination
            ],
            scroll=ft.ScrollMode.AUTO
        )
    
    def load_users(self, page: int = 1, search: str = ""):
        try:
            response = requests.get(
                f"{API_BASE_URL}/users",
                headers=self.headers,
                params={"skip": (page-1)*10, "limit": 10, "search": search}
            )
            if response.status_code == 200:
                data = response.json()
                self.update_users_table(data["items"])
            else:
                self.show_error(f"Error loading users: {response.text}")
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
    
    def load_chat_history(self, page: int = 1, search: str = ""):
        try:
            response = requests.get(
                f"{API_BASE_URL}/chat-history",
                headers=self.headers,
                params={"skip": (page-1)*10, "limit": 10, "search": search}
            )
            if response.status_code == 200:
                data = response.json()
                self.update_chat_table(data["items"])
            else:
                self.show_error(f"Error loading chat history: {response.text}")
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
    
    def update_users_table(self, users):
        self.users_table.rows.clear()
        for user in users:
            self.users_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(user["id"]))),
                        ft.DataCell(ft.Text(user["username"])),
                        ft.DataCell(ft.Text(user["email"])),
                        ft.DataCell(ft.Text("Active" if user["is_active"] else "Inactive")),
                        ft.DataCell(ft.Text(datetime.fromisoformat(user["created_at"]).strftime("%Y-%m-%d %H:%M"))),
                        ft.DataCell(
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.icons.EDIT,
                                        on_click=lambda u=user: self.edit_user(u)
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.DELETE,
                                        on_click=lambda u=user: self.delete_user(u)
                                    )
                                ]
                            )
                        )
                    ]
                )
            )
        self.page.update()
    
    def update_chat_table(self, chats):
        self.chat_table.rows.clear()
        for chat in chats:
            self.chat_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(chat["id"]))),
                        ft.DataCell(ft.Text(str(chat["user_id"]))),
                        ft.DataCell(ft.Text(chat["message"][:50] + "..." if len(chat["message"]) > 50 else chat["message"])),
                        ft.DataCell(ft.Text(chat["response"][:50] + "..." if len(chat["response"]) > 50 else chat["response"])),
                        ft.DataCell(ft.Text(datetime.fromisoformat(chat["created_at"]).strftime("%Y-%m-%d %H:%M"))),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.icons.IMAGE,
                                on_click=lambda c=chat: self.view_image(c) if c["image_path"] else None
                            ) if chat["image_path"] else ft.Text("No image")
                        )
                    ]
                )
            )
        self.page.update()
    
    def search_users(self, e):
        self.load_users(search=e.control.value)
    
    def search_chat_history(self, e):
        self.load_chat_history(search=e.control.value)
    
    def change_page(self, delta):
        current_page = int(self.page_number.value)
        new_page = current_page + delta
        if new_page > 0:
            self.page_number.value = str(new_page)
            self.load_users(page=new_page)
            self.page.update()
    
    def change_chat_page(self, delta):
        current_page = int(self.chat_page_number.value)
        new_page = current_page + delta
        if new_page > 0:
            self.chat_page_number.value = str(new_page)
            self.load_chat_history(page=new_page)
            self.page.update()
    
    def edit_user(self, user):
        def save_changes(e):
            try:
                update_data = {
                    "email": email_field.value,
                    "username": username_field.value,
                    "is_active": is_active.value,
                    "is_admin": is_admin.value
                }
                
                if password_field.value:
                    update_data["password"] = password_field.value
                
                response = requests.put(
                    f"{API_BASE_URL}/users/{user['id']}",
                    headers=self.headers,
                    json=update_data
                )
                
                if response.status_code == 200:
                    dialog.open = False
                    self.load_users()
                    self.show_error("User updated successfully")
                else:
                    self.show_error(f"Error updating user: {response.text}")
            except Exception as e:
                self.show_error(f"Error: {str(e)}")
            self.page.update()
        
        # Create dialog content
        email_field = ft.TextField(label="Email", value=user["email"])
        username_field = ft.TextField(label="Username", value=user["username"])
        password_field = ft.TextField(label="New Password (optional)", password=True)
        is_active = ft.Switch(label="Active", value=user["is_active"])
        is_admin = ft.Switch(label="Admin", value=user["is_admin"])
        
        dialog = ft.AlertDialog(
            title=ft.Text("Edit User"),
            content=ft.Column(
                [
                    email_field,
                    username_field,
                    password_field,
                    is_active,
                    is_admin
                ],
                tight=True,
                spacing=20
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.TextButton("Save", on_click=save_changes)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def delete_user(self, user):
        def confirm_delete(e):
            try:
                response = requests.delete(
                    f"{API_BASE_URL}/users/{user['id']}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    dialog.open = False
                    self.load_users()
                    self.show_error("User deleted successfully")
                else:
                    self.show_error(f"Error deleting user: {response.text}")
            except Exception as e:
                self.show_error(f"Error: {str(e)}")
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Are you sure you want to delete user {user['username']}?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.TextButton("Delete", on_click=confirm_delete)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def view_image(self, chat):
        if not chat["image_path"]:
            return
        
        dialog = ft.AlertDialog(
            title=ft.Text("Image View"),
            content=ft.Image(
                src=chat["image_path"],
                width=400,
                height=400,
                fit=ft.ImageFit.CONTAIN
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: setattr(dialog, 'open', False))
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def show_error(self, message):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()
    
    def logout(self, e):
        # Clear auth token and redirect to login
        self.auth_token = None
        self.page.go("/login")

def main(page: ft.Page):
    # Configure the page
    page.title = "Admin Dashboard"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window_width = 1200
    page.window_height = 800
    page.window_resizable = True
    
    # Get auth token from environment or configuration
    auth_token = "your-auth-token"  # Replace with actual token
    
    # Initialize admin page
    admin_page = AdminPage(page, auth_token)
    
    # Initialize page numbers
    admin_page.page_number = ft.Text("1")
    admin_page.chat_page_number = ft.Text("1")
    
    # Load initial data
    admin_page.load_users()
    admin_page.load_chat_history()

if __name__ == "__main__":
    ft.app(target=main) 