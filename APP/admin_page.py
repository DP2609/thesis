# admin_page.py
import flet as ft
import requests

# API configuration
API_BASE_URL = "http://localhost:8000"  # Điều chỉnh URL API server của bạn

class AdminPage(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="/admin")
        self.page = page
        self.vertical_alignment = ft.MainAxisAlignment.START
        self.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

        # Lấy thông tin từ session
        self.username = self.page.session.get("username") or "Admin"
        self.token = self.page.session.get("token")

        # Khởi tạo dữ liệu
        self.users = []
        self.history = []
        self.current_tab = "users"  # Tab mặc định

        # Tạo nút đăng xuất
        self.logout_button = ft.ElevatedButton("Đăng xuất", on_click=self.logout_clicked)

        # AppBar được gán cho thuộc tính appbar của View
        self.appbar = ft.AppBar(
            title=ft.Text("Trang Quản Trị"),
            bgcolor=ft.Colors.BLUE_GREY_100,  # Màu khác cho admin
            actions=[self.logout_button]
        )

        # Tạo các tab dọc bên trái
        self.side_tabs = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Text(f"Quản trị viên\n{self.username}", 
                        size=16,
                        text_align=ft.TextAlign.CENTER,
                        weight=ft.FontWeight.BOLD
                    ),
                    padding=20,
                    bgcolor=ft.Colors.BLUE_GREY_100,
                    border_radius=ft.BorderRadius(0, 10, 0, 0),  # Top-right corner radius set to 10
                ),
                ft.ElevatedButton(
                    text="Quản lý người dùng",
                    icon=ft.Icons.PEOPLE,
                    on_click=lambda e: self.change_tab("users"),
                    width=200,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=0),
                    ),
                ),
                ft.ElevatedButton(
                    text="Lịch sử phát hiện",
                    icon=ft.Icons.HISTORY,
                    on_click=lambda e: self.change_tab("history"),
                    width=200,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=0),
                    ),
                ),
                ft.Container(expand=True),  # Spacer
                self.logout_button,
            ],
            width=200,
            # bgcolor=ft.Colors.BLUE_GREY_50,
            height=float("inf"),
        )

        # Tạo container cho nội dung tab
        self.tab_content = ft.Container(
            expand=True,
            padding=20,
        )

        # Tạo các thành phần UI cho tab người dùng
        self.users_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Tên người dùng")),
                ft.DataColumn(ft.Text("Email")),
                ft.DataColumn(ft.Text("Vai trò")),
                ft.DataColumn(ft.Text("Hành động"))
            ],
            rows=[]
        )

        # Tạo các thành phần UI cho tab lịch sử
        self.history_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Người dùng")),
                ft.DataColumn(ft.Text("Thời gian")),
                ft.DataColumn(ft.Text("Kết quả")),
                ft.DataColumn(ft.Text("Hành động"))
            ],
            rows=[]
        )

        # Tạo layout chính với Row để chia 2 phần
        self.controls = [
            ft.Row(
                [
                    self.side_tabs,
                    ft.VerticalDivider(width=1),
                    self.tab_content,
                ],
                expand=True,
            )
        ]

        # Tải dữ liệu ban đầu
        self.load_users()
        self.update_tab_content()

    def get_auth_header(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def change_tab(self, tab_name: str):
        self.current_tab = tab_name
        if tab_name == "users":
            self.load_users()
        else:
            self.load_history()
        self.update_tab_content()

    def update_tab_content(self):
        if self.current_tab == "users":
            # Hiển thị tab người dùng
            self.tab_content.content = self.create_users_content()
        else:
            # Hiển thị tab lịch sử
            self.tab_content.content = self.create_history_content()
        self.page.update()

    def create_users_content(self):
        # Cập nhật bảng người dùng
        self.users_table.rows = []
        for user in self.users:
            self.users_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(user.get("id", "")))),
                        ft.DataCell(ft.Text(user.get("username", ""))),
                        ft.DataCell(ft.Text(user.get("email", ""))),
                        ft.DataCell(ft.Text("Admin" if user.get("is_admin") else "Người dùng")),
                        ft.DataCell(
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT,
                                        tooltip="Chỉnh sửa",
                                        on_click=lambda e, u=user: self.edit_user(u)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        tooltip="Xóa",
                                        on_click=lambda e, u=user: self.delete_user(u)
                                    )
                                ]
                            )
                        )
                    ]
                )
            )

        # Tạo nút thêm người dùng
        add_user_button = ft.ElevatedButton(
            "Thêm người dùng",
            icon=ft.Icons.ADD,
            on_click=self.add_user
        )

        # Tạo layout cho nội dung
        return ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text("Danh sách người dùng", 
                                  size=24, 
                                  weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            add_user_button,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    margin=ft.margin.only(bottom=20)
                ),
                ft.Container(
                    content=ft.Column(
                        [self.users_table],
                        scroll=ft.ScrollMode.AUTO,
                        expand=True
                    ),
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=10,
                    padding=10,
                    expand=True
                ),
            ],
            expand=True
        )

    def create_history_content(self):
        # Cập nhật bảng lịch sử
        self.history_table.rows = []
        for item in self.history:
            self.history_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(item.get("id", "")))),
                        ft.DataCell(ft.Text(item.get("username", ""))),
                        ft.DataCell(ft.Text(item.get("timestamp", ""))),
                        ft.DataCell(ft.Text(item.get("result", "")[:20] + "...")),
                        ft.DataCell(
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.Icons.VISIBILITY,
                                        tooltip="Xem chi tiết",
                                        on_click=lambda e, i=item: self.view_history_detail(i)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        tooltip="Xóa",
                                        on_click=lambda e, i=item: self.delete_history(i)
                                    )
                                ]
                            )
                        )
                    ]
                )
            )

        # Tạo layout cho nội dung
        return ft.Column(
            [
                ft.Container(
                    content=ft.Text("Lịch sử phát hiện", 
                                  size=24, 
                                  weight=ft.FontWeight.BOLD),
                    margin=ft.margin.only(bottom=20)
                ),
                ft.Container(
                    content=ft.Column(
                        [self.history_table],
                        scroll=ft.ScrollMode.AUTO,
                        expand=True
                    ),
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=10,
                    padding=10,
                    expand=True
                ),
            ],
            expand=True
        )

    def load_users(self):
        try:
            # Gọi API để lấy danh sách người dùng
            headers = self.get_auth_header()
            response = requests.get(f"{API_BASE_URL}/users", headers=headers)
            
            if response.status_code == 200:
                self.users = response.json()
            else:
                # Dữ liệu mẫu nếu API không hoạt động
                self.users = [
                    {"id": 1, "username": "admin", "email": "admin@example.com", "is_admin": True},
                    {"id": 2, "username": "user1", "email": "user1@example.com", "is_admin": False},
                    {"id": 3, "username": "user2", "email": "user2@example.com", "is_admin": False}
                ]
        except Exception as e:
            print(f"Error loading users: {str(e)}")
            # Dữ liệu mẫu nếu có lỗi
            self.users = [
                {"id": 1, "username": "admin", "email": "admin@example.com", "is_admin": True},
                {"id": 2, "username": "user1", "email": "user1@example.com", "is_admin": False},
                {"id": 3, "username": "user2", "email": "user2@example.com", "is_admin": False}
            ]

    def load_history(self):
        try:
            # Gọi API để lấy lịch sử
            headers = self.get_auth_header()
            response = requests.get(f"{API_BASE_URL}/history", headers=headers)
            
            if response.status_code == 200:
                self.history = response.json()
            else:
                # Dữ liệu mẫu nếu API không hoạt động
                self.history = [
                    {"id": 1, "username": "user1", "timestamp": "2023-05-01 10:30:45", "result": "Phát hiện: Hình ảnh chứa nội dung không phù hợp"},
                    {"id": 2, "username": "user2", "timestamp": "2023-05-02 14:22:10", "result": "Phát hiện: Hình ảnh an toàn"},
                    {"id": 3, "username": "admin", "timestamp": "2023-05-03 09:15:30", "result": "Phát hiện: Hình ảnh chứa nội dung bạo lực"}
                ]
        except Exception as e:
            print(f"Error loading history: {str(e)}")
            # Dữ liệu mẫu nếu có lỗi
            self.history = [
                {"id": 1, "username": "user1", "timestamp": "2023-05-01 10:30:45", "result": "Phát hiện: Hình ảnh chứa nội dung không phù hợp"},
                {"id": 2, "username": "user2", "timestamp": "2023-05-02 14:22:10", "result": "Phát hiện: Hình ảnh an toàn"},
                {"id": 3, "username": "admin", "timestamp": "2023-05-03 09:15:30", "result": "Phát hiện: Hình ảnh chứa nội dung bạo lực"}
            ]

    def add_user(self, e=None):
        # Hiển thị dialog thêm người dùng
        def close_dlg(e):
            dlg.open = False
            self.page.update()

        def save_user(e):
            # Xử lý lưu người dùng mới
            username = username_field.value
            email = email_field.value
            password = password_field.value
            is_admin = admin_checkbox.value

            if username and email and password:
                # Gọi API để thêm người dùng
                try:
                    headers = self.get_auth_header()
                    data = {
                        "username": username,
                        "email": email,
                        "password": password,
                        "is_admin": is_admin
                    }
                    # Trong thực tế, bạn sẽ gọi API ở đây
                    # response = requests.post(f"{API_BASE_URL}/users", json=data, headers=headers)
                    
                    # Giả lập thêm người dùng thành công
                    new_id = max([user.get("id", 0) for user in self.users]) + 1
                    self.users.append({
                        "id": new_id,
                        "username": username,
                        "email": email,
                        "is_admin": is_admin
                    })
                    
                    close_dlg(e)
                    self.update_tab_content()
                except Exception as ex:
                    print(f"Error adding user: {str(ex)}")
            else:
                error_text.value = "Vui lòng điền đầy đủ thông tin"
                self.page.update()

        username_field = ft.TextField(label="Tên người dùng", autofocus=True)
        email_field = ft.TextField(label="Email")
        password_field = ft.TextField(label="Mật khẩu", password=True, can_reveal_password=True)
        admin_checkbox = ft.Checkbox(label="Là quản trị viên")
        error_text = ft.Text("", color=ft.Colors.RED)

        dlg = ft.AlertDialog(
            title=ft.Text("Thêm người dùng mới"),
            content=ft.Column(
                [
                    username_field,
                    email_field,
                    password_field,
                    admin_checkbox,
                    error_text
                ],
                tight=True,
                spacing=20,
                width=400
            ),
            actions=[
                ft.TextButton("Hủy", on_click=close_dlg),
                ft.ElevatedButton("Lưu", on_click=save_user)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def edit_user(self, user):
        # Hiển thị dialog chỉnh sửa người dùng
        def close_dlg(e):
            dlg.open = False
            self.page.update()

        def save_user(e):
            # Xử lý lưu thông tin người dùng
            username = username_field.value
            email = email_field.value
            is_admin = admin_checkbox.value

            if username and email:
                # Gọi API để cập nhật người dùng
                try:
                    headers = self.get_auth_header()
                    data = {
                        "username": username,
                        "email": email,
                        "is_admin": is_admin
                    }
                    # Trong thực tế, bạn sẽ gọi API ở đây
                    # response = requests.put(f"{API_BASE_URL}/users/{user['id']}", json=data, headers=headers)
                    
                    # Giả lập cập nhật người dùng thành công
                    for u in self.users:
                        if u.get("id") == user.get("id"):
                            u["username"] = username
                            u["email"] = email
                            u["is_admin"] = is_admin
                            break
                    
                    close_dlg(e)
                    self.update_tab_content()
                except Exception as ex:
                    print(f"Error updating user: {str(ex)}")
            else:
                error_text.value = "Vui lòng điền đầy đủ thông tin"
                self.page.update()

        username_field = ft.TextField(label="Tên người dùng", value=user.get("username", ""))
        email_field = ft.TextField(label="Email", value=user.get("email", ""))
        admin_checkbox = ft.Checkbox(label="Là quản trị viên", value=user.get("is_admin", False))
        error_text = ft.Text("", color=ft.Colors.RED)

        dlg = ft.AlertDialog(
            title=ft.Text("Chỉnh sửa người dùng"),
            content=ft.Column(
                [
                    username_field,
                    email_field,
                    admin_checkbox,
                    error_text
                ],
                tight=True,
                spacing=20,
                width=400
            ),
            actions=[
                ft.TextButton("Hủy", on_click=close_dlg),
                ft.ElevatedButton("Lưu", on_click=save_user)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def delete_user(self, user):
        # Hiển thị dialog xác nhận xóa người dùng
        def close_dlg(e):
            dlg.open = False
            self.page.update()

        def confirm_delete(e):
            # Gọi API để xóa người dùng
            try:
                headers = self.get_auth_header()
                # Trong thực tế, bạn sẽ gọi API ở đây
                # response = requests.delete(f"{API_BASE_URL}/users/{user['id']}", headers=headers)
                
                # Giả lập xóa người dùng thành công
                self.users = [u for u in self.users if u.get("id") != user.get("id")]
                
                close_dlg(e)
                self.update_tab_content()
            except Exception as ex:
                print(f"Error deleting user: {str(ex)}")

        dlg = ft.AlertDialog(
            title=ft.Text("Xác nhận xóa"),
            content=ft.Text(f"Bạn có chắc chắn muốn xóa người dùng {user.get('username')}?"),
            actions=[
                ft.TextButton("Hủy", on_click=close_dlg),
                ft.ElevatedButton("Xóa", on_click=confirm_delete, color=ft.Colors.RED)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def view_history_detail(self, history_item):
        # Hiển thị dialog chi tiết lịch sử
        def close_dlg(e):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text(f"Chi tiết lịch sử #{history_item.get('id')}"),
            content=ft.Column(
                [
                    ft.Text(f"Người dùng: {history_item.get('username')}"),
                    ft.Text(f"Thời gian: {history_item.get('timestamp')}"),
                    ft.Container(height=10),
                    ft.Text("Kết quả phát hiện:"),
                    ft.Container(
                        content=ft.Text(history_item.get('result', '')),
                        padding=10,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=5,
                        width=400
                    )
                ],
                tight=True,
                spacing=10,
                width=400
            ),
            actions=[
                ft.TextButton("Đóng", on_click=close_dlg)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def delete_history(self, history_item):
        # Hiển thị dialog xác nhận xóa lịch sử
        def close_dlg(e):
            dlg.open = False
            self.page.update()

        def confirm_delete(e):
            # Gọi API để xóa lịch sử
            try:
                headers = self.get_auth_header()
                # Trong thực tế, bạn sẽ gọi API ở đây
                # response = requests.delete(f"{API_BASE_URL}/history/{history_item['id']}", headers=headers)
                
                # Giả lập xóa lịch sử thành công
                self.history = [h for h in self.history if h.get("id") != history_item.get("id")]
                
                close_dlg(e)
                self.update_tab_content()
            except Exception as ex:
                print(f"Error deleting history: {str(ex)}")

        dlg = ft.AlertDialog(
            title=ft.Text("Xác nhận xóa"),
            content=ft.Text(f"Bạn có chắc chắn muốn xóa mục lịch sử này?"),
            actions=[
                ft.TextButton("Hủy", on_click=close_dlg),
                ft.ElevatedButton("Xóa", on_click=confirm_delete, color=ft.Colors.RED)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def logout_clicked(self, e):
        self.page.session.clear()
        self.page.go("/login")

if __name__ == "__main__":
    def main(page: ft.Page):
        page.title = "Test Admin Page"
        page.session.set("username", "TestUserAdmin")
        page.session.set("token", "test_token")  # Thêm token giả để test
        admin_view = AdminPage(page)
        page.views.append(admin_view)
        page.update()
    ft.app(target=main)