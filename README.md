# Đề tài 1: Hệ thống Quản lý Thư viện (Library Management System)
- **Học phần:** Triển khai và Quản trị Hệ thống Phần mềm
- **Sinh viên thực hiện:** Trần Duy Hiếu - MSSV: dtc245299555
- **Công nghệ triển khai:** FastAPI, PostgreSQL, pgAdmin, Nginx, Prometheus, Grafana, Loki.

## Hướng dẫn khởi chạy
1. Khởi động toàn bộ container:
   \`\`\`bash
   docker compose up -d --build
   \`\`\`
2. Địa chỉ truy cập:
   - Web Quản lý Thư viện (qua Nginx): \`http://<IP_MÁY_ẢO>\`
   - pgAdmin: \`http://<IP_MÁY_ẢO>:5050\`
   - Prometheus: \`http://<IP_MÁY_ẢO>:9090\`
   - Grafana: \`http://<IP_MÁY_ẢO>:3000\`
