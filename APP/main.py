# main.py
import flet as ft
from register_page import RegisterPage
from login_page import LoginPage  # Import class
from client_page import ClientPage  # Import class
from admin_page import AdminPage  # Import class

def main(page: ft.Page):
    page.title = "Ứng dụng Flet Đa Trang (Class)"
    # Các cài đặt alignment toàn cục cho page có thể không cần thiết
    # nếu mỗi View tự quản lý alignment của nó.
    # page.vertical_alignment = ft.MainAxisAlignment.CENTER
    # page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Ánh xạ route tới các Class View tương ứng
    app_routes = {
        "/login": LoginPage,  # Trỏ tới class, không phải instance
        "/client": ClientPage,
        "/admin": AdminPage,
        "/register": RegisterPage,  # Chưa có class cho trang này
    }

    def route_change(route_event: ft.RouteChangeEvent):
        page.views.clear()

        # Lấy Class View từ app_routes dựa trên route mới
        # Nếu không tìm thấy, mặc định về LoginPage
        ViewClass = app_routes.get(route_event.route, LoginPage)

        # Tạo một instance của Class View đó
        # Class View này đã kế thừa từ ft.View
        current_view_instance = ViewClass(page) # Truyền `page` vào constructor
        page.views.append(current_view_instance)

        # Kiểm tra quyền truy cập cho các trang bảo vệ
        current_route = page.route # Lấy route hiện tại của page
        user_role = page.session.get("user_role")

        # Nếu đang ở trang login mà đã có role, chuyển hướng phù hợp
        if current_route == "/login" and user_role:
            if user_role == "admin":
                page.go("/admin")
                return # Dừng xử lý tiếp, vì page.go sẽ trigger route_change mới
            else:
                page.go("/client")
                return # Dừng xử lý tiếp

        # Bảo vệ các trang admin và client
        if current_route == "/admin" and user_role != "admin":
            page.go("/login") # Điều hướng về login, route_change sẽ xử lý việc hiển thị LoginPage
            return
        elif current_route == "/client" and not user_role: # Chỉ cần có user_role là được vào client
            page.go("/login")
            return
        # Nếu người dùng admin cố vào /client, hoặc user vào /admin (đã xử lý ở trên)
        # hoặc các trường hợp khác không mong muốn, có thể thêm logic ở đây.
        # Hiện tại, nếu admin vào /client thì vẫn được, và user vào /admin sẽ bị đẩy về /login.

        page.update()
        
    page.on_route_change = route_change

    # Khởi đầu ứng dụng
    # Kiểm tra session để quyết định route ban đầu
    initial_role = page.session.get("user_role")
    if initial_role == "admin":
        page.go("/admin")
    elif initial_role: # Bất kỳ role nào khác admin (ví dụ "user")
        page.go("/client")
    else:
        page.go("/login")

if __name__ == "__main__":
    # ft.app(target=main, view=ft.AppView.FLET_APP_WEB)
    ft.app(target=main) # Cho desktop