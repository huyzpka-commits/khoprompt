# KhoPrompt

Website tổng hợp, tìm kiếm và chia sẻ **prompt tạo ảnh/video bằng AI**.

Mỗi prompt có ảnh demo, bộ lọc theo công cụ AI, tìm kiếm nhanh, và chỉ cần click để mở modal sao chép prompt.

---

## Tính năng

- 🔎 **Tìm kiếm thông minh**: tìm theo từ khóa, công cụ, tag, mô tả hoặc nội dung prompt.
- 🏷️ **Lọc theo AI tool**: Gemini, ChatGPT, Flux, Midjourney, Stable Diffusion, Nano Banana, Khác.
- 📋 **Sao chép 1 click**: click ảnh/card mở modal, nhấn "Sao chép" là có prompt.
- 🖼️ **Ảnh demo minh họa**: hiển thị ảnh kết quả trước khi dùng.
- 📄 **Phân trang**: hỗ trợ dataset lớn (20/40/60/100 mục/trang).
- 🔄 **Cập nhật dữ liệu**: scraper tự động lấy prompt từ `app.revidapi.com/prompts`.

---

## Công nghệ

- **Frontend**: HTML5, CSS3 (responsive, dark mode), Vanilla JavaScript (không framework).
- **Data**: JSON tĩnh (`data/prompts.json`).
- **Scraper**: Python 3 + thư viện chuẩn (`urllib`, `json`).
- **Deployment**: bất kỳ static host nào (Cloudflare Pages, GitHub Pages, Netlify, Vercel, Nginx, ...).

---

## Cấu trúc dự án

```
khoprompt/
├── index.html              # Giao diện chính
├── css/
│   └── style.css           # Styles responsive
├── js/
│   └── app.js              # Logic tìm kiếm, lọc, modal, phân trang
├── data/
│   ├── prompts.json        # Dữ liệu prompt website (đã scrape + mẫu)
│   ├── prompts_details.json# Cache detail từ API (dùng để resume)
│   └── revid_prompts_raw.json
├── assets/
│   ├── placeholders/       # Ảnh demo SVG mẫu
│   └── revid/              # Ảnh demo tải về từ revidapi
├── tools/
│   ├── scraper.py          # Scraper chính
│   └── test_server.py      # Script kiểm tra server
└── .gitignore
```

---

## Chạy thử nhanh

```bash
# Vào thư mục dự án
cd khoprompt

# Khởi động server tĩnh
python -m http.server 8080
```

Mở trình duyệt tại: [http://localhost:8080](http://localhost:8080)

---

## Scraper: Lấy dữ liệu từ app.revidapi.com

### Cảnh báo

- `robots.txt` của `app.revidapi.com` **disallow `/api/`** cho tất cả user-agent.
- Trang có **20,717+ prompt**. Việc scrape toàn bộ sẽ tạo ra **20,717 request detail**.
- Chỉ nên chạy full scrape khi có sự cho phép của chủ site, hoặc với tốc độ rất chậm (`--delay` cao).
- Scraper được viết với **delay cấu hình**, **resume**, và **retry** để giảm thiểu tải server.

### Cách dùng

```bash
# Lấy 100 prompt mới nhất + ảnh demo về local
python tools/scraper.py --max-items 100 --delay 0.6 --download-images --image-delay 0.3

# Lấy 500 prompt, dùng URL ảnh gốc (không tải ảnh)
python tools/scraper.py --max-items 500 --delay 0.6

# Lấy tất cả prompt (20,717) — CHỈ CHẠY KHI ĐÃ ĐƯỢC CHO PHÉP
python tools/scraper.py --max-items 0 --delay 1.5 --download-images --image-delay 0.5
```

### Tham số scraper

| Tham số | Mặc định | Mô tả |
|---------|----------|-------|
| `--max-items` | 100 | Số lượng prompt tối đa (`0` = không giới hạn) |
| `--limit` | 50 | Số item mỗi trang list API |
| `--delay` | 0.8 | Delay giữa các request detail (giây) |
| `--page-delay` | 1.0 | Delay giữa các trang list API |
| `--image-delay` | 0.5 | Delay giữa các lần tải ảnh |
| `--download-images` | false | Tải ảnh demo về local |
| `--images-dir` | `assets/revid` | Thư mục lưu ảnh |
| `--output` | `data/prompts.json` | File JSON đầu ra cho website |
| `--raw-output` | `data/revid_prompts_raw.json` | Cache list API |
| `--resume` | false | Tiếp tục từ file cache đã có |
| `--media-type` | `image` | Lọc `image`, `video`, hoặc `all` |

### Output scraper

- `data/prompts.json` — dữ liệu chuẩn hóa cho website.
- `data/prompts_details.json` — cache detail để resume lại sau này.
- `data/revid_prompts_raw.json` — cache list từ API.
- `assets/revid/` — ảnh demo (nếu bật `--download-images`).

### Ví dụ pipeline cập nhật định kỳ

```bash
# Chạy 1 lần/ngày lấy 500 prompt mới
python tools/scraper.py --max-items 500 --delay 0.6 --download-images --image-delay 0.3
```

Sau đó commit `data/prompts.json` và `assets/revid/` (nếu dùng ảnh local) lên repo.

---

## API nguồn

Trang `app.revidapi.com/prompts` sử dụng 2 endpoint:

- `GET https://app.revidapi.com/api/prompts?page={page}&limit={limit}`
- `GET https://app.revidapi.com/api/prompts/{id}`

Trường dữ liệu quan trọng:

- `title`: tiêu đề prompt
- `prompt_text`: nội dung prompt đầy đủ
- `description`: mô tả
- `negative_prompt`: negative prompt (nếu có)
- `model`: model AI được sử dụng
- `media_type`: `image` hoặc `video`
- `output_url`: URL ảnh demo
- `category`: thể loại
- `likes_count`, `views_count`: độ phổ biến

---

## Lưu ý quy mô

| Số lượng prompt | Dung lượng ảnh gợi ý | Chiến lược ảnh |
|-----------------|----------------------|----------------|
| < 500 | < 500 MB | Tải ảnh local (`--download-images`) |
| 500 – 2.000 | 500 MB – 2 GB | Cân nhắc tải local hoặc dùng URL gốc |
| > 2.000 | > 2 GB | **Nên dùng URL gốc** hoặc lưu lên R2/S3/CDN |

Với dataset lớn, hãy bỏ `--download-images` để giữ `image` là URL gốc từ `cdn.tramsangtao.com` / `img.opennana.com`.

---

## Deployment

Dự án là static site, có thể deploy lên bất kỳ nơi nào:

- **Cloudflare Pages**: kéo thả thư mục hoặc dùng Wrangler.
- **GitHub Pages**: bật Pages trong repo settings.
- **Netlify / Vercel**: connect repo hoặc upload thư mục.
- **Nginx / Apache**: copy thư mục đến web root.

---

## Đóng góp & License

- Dự án mã nguồn mở để phục vụ cộng đồng prompt AI.
- Dữ liệu prompt thuộc về tác giả gốc trên `app.revidapi.com` — chỉ sử dụng cho mục đích tham khảo và cá nhân hóa.

---

<p align="center">
  <strong>KhoPrompt</strong> — Kho prompt AI dễ tìm, dễ copy.
</p>
