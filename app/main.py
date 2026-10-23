import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Cấu hình Logging chuẩn cho Loki + Promtail
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] service=library-web %(message)s"
)
logger = logging.getLogger("library-web")

app = FastAPI(title="Hệ thống Quản lý Thư viện")

# Prometheus Metrics
REQUEST_COUNT = Counter("library_http_requests_total", "Total HTTP Requests", ["method", "endpoint"])
BORROW_COUNT = Counter("library_book_borrows_total", "Total Books Borrowed")
RETURN_COUNT = Counter("library_book_returns_total", "Total Books Returned")

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        database=os.getenv("DB_NAME", "library_db"),
        user=os.getenv("DB_USER", "app_user"),
        password=os.getenv("DB_PASSWORD", "AppStrongPassword_2026!"),
        cursor_factory=RealDictCursor
    )

@app.middleware("http")
async def log_and_metric_middleware(request: Request, call_next):
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    response = await call_next(request)
    logger.info(f"method={request.method} path={request.url.path} status={response.status_code}")
    return response

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/", response_class=HTMLResponse)
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM books ORDER BY id ASC;")
    books = cur.fetchall()
    
    cur.execute("SELECT * FROM readers ORDER BY id ASC;")
    readers = cur.fetchall()
    
    cur.execute("""
        SELECT br.id, b.title, r.full_name, br.borrow_date, br.return_date, br.status
        FROM borrow_records br
        JOIN books b ON br.book_id = b.id
        JOIN readers r ON br.reader_id = r.id
        ORDER BY br.id DESC;
    """)
    borrows = cur.fetchall()
    
    cur.close()
    conn.close()

    books_rows = "".join([f"<tr><td>{b['id']}</td><td>{b['title']}</td><td>{b['author']}</td><td>{b['quantity']}</td></tr>" for b in books])
    readers_rows = "".join([f"<tr><td>{r['id']}</td><td>{r['full_name']}</td><td>{r['email']}</td></tr>" for r in readers])
    
    borrows_rows = ""
    for br in borrows:
        action_btn = (
            f"<form method='post' action='/return/{br['id']}' style='margin:0;'>"
            f"<button type='submit' class='btn btn-sm btn-success'>Trả sách</button></form>"
            if br["status"] == "BORROWED" else "<span class='badge bg-secondary'>Đã trả</span>"
        )
        borrows_rows += f"<tr><td>{br['id']}</td><td>{br['title']}</td><td>{br['full_name']}</td><td>{br['status']}</td><td>{action_btn}</td></tr>"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Hệ thống Quản lý Thư viện</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container py-4">
            <h2 class="mb-4 text-primary">📚 Hệ thống Quản lý Thư viện</h2>
            <div class="row g-4">
                <!-- Quản lý Sách -->
                <div class="col-md-6">
                    <div class="card shadow-sm">
                        <div class="card-header bg-dark text-white">Quản lý Sách</div>
                        <div class="card-body">
                            <form method="post" action="/books" class="row g-2 mb-3">
                                <div class="col-5"><input type="text" name="title" class="form-control" placeholder="Tên sách" required></div>
                                <div class="col-4"><input type="text" name="author" class="form-control" placeholder="Tác giả" required></div>
                                <div class="col-3"><input type="number" name="quantity" class="form-control" placeholder="SL" min="1" required></div>
                                <div class="col-12"><button type="submit" class="btn btn-primary btn-sm w-100">Thêm Sách</button></div>
                            </form>
                            <table class="table table-bordered table-sm">
                                <thead><tr><th>ID</th><th>Tên sách</th><th>Tác giả</th><th>Tồn kho</th></tr></thead>
                                <tbody>{books_rows}</tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Quản lý Độc giả -->
                <div class="col-md-6">
                    <div class="card shadow-sm">
                        <div class="card-header bg-dark text-white">Quản lý Độc giả</div>
                        <div class="card-body">
                            <form method="post" action="/readers" class="row g-2 mb-3">
                                <div class="col-6"><input type="text" name="full_name" class="form-control" placeholder="Họ tên độc giả" required></div>
                                <div class="col-6"><input type="email" name="email" class="form-control" placeholder="Email" required></div>
                                <div class="col-12"><button type="submit" class="btn btn-primary btn-sm w-100">Thêm Độc giả</button></div>
                            </form>
                            <table class="table table-bordered table-sm">
                                <thead><tr><th>ID</th><th>Họ tên</th><th>Email</th></tr></thead>
                                <tbody>{readers_rows}</tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Quản lý Mượn / Trả sách -->
                <div class="col-12">
                    <div class="card shadow-sm">
                        <div class="card-header bg-primary text-white">Quản lý Mượn / Trả Sách</div>
                        <div class="card-body">
                            <form method="post" action="/borrow" class="row g-2 mb-3">
                                <div class="col-5"><input type="number" name="book_id" class="form-control" placeholder="Nhập ID Sách" required></div>
                                <div class="col-5"><input type="number" name="reader_id" class="form-control" placeholder="Nhập ID Độc giả" required></div>
                                <div class="col-2"><button type="submit" class="btn btn-warning w-100">Mượn Sách</button></div>
                            </form>
                            <table class="table table-striped table-sm">
                                <thead><tr><th>Mã phiếu</th><th>Sách</th><th>Độc giả</th><th>Trạng thái</th><th>Thao tác</th></tr></thead>
                                <tbody>{borrows_rows}</tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/books")
def add_book(title: str = Form(...), author: str = Form(...), quantity: int = Form(...)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO books (title, author, quantity) VALUES (%s, %s, %s);", (title, author, quantity))
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"action=add_book title='{title}' quantity={quantity}")
    return RedirectResponse(url="/", status_code=303)

@app.post("/readers")
def add_reader(full_name: str = Form(...), email: str = Form(...)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO readers (full_name, email) VALUES (%s, %s);", (full_name, email))
        conn.commit()
        logger.info(f"action=add_reader email='{email}'")
    except Exception as e:
        conn.rollback()
        logger.error(f"action=add_reader_failed error='{str(e)}'")
    finally:
        cur.close()
        conn.close()
    return RedirectResponse(url="/", status_code=303)

@app.post("/borrow")
def borrow_book(book_id: int = Form(...), reader_id: int = Form(...)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT quantity FROM books WHERE id = %s;", (book_id,))
    book = cur.fetchone()
    if book and book["quantity"] > 0:
        cur.execute("UPDATE books SET quantity = quantity - 1 WHERE id = %s;", (book_id,))
        cur.execute("INSERT INTO borrow_records (book_id, reader_id) VALUES (%s, %s);", (book_id, reader_id))
        conn.commit()
        BORROW_COUNT.inc()
        logger.info(f"action=borrow_book status=success book_id={book_id} reader_id={reader_id}")
    else:
        logger.warning(f"action=borrow_book status=failed_out_of_stock book_id={book_id} reader_id={reader_id}")
    cur.close()
    conn.close()
    return RedirectResponse(url="/", status_code=303)

@app.post("/return/{record_id}")
def return_book(record_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT book_id, status FROM borrow_records WHERE id = %s;", (record_id,))
    record = cur.fetchone()
    if record and record["status"] == "BORROWED":
        cur.execute("UPDATE borrow_records SET status = 'RETURNED', return_date = CURRENT_TIMESTAMP WHERE id = %s;", (record_id,))
        cur.execute("UPDATE books SET quantity = quantity + 1 WHERE id = %s;", (record["book_id"],))
        conn.commit()
        RETURN_COUNT.inc()
        logger.info(f"action=return_book status=success record_id={record_id}")
    cur.close()
    conn.close()
    return RedirectResponse(url="/", status_code=303)