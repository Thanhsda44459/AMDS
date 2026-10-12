# TEST-001: một lệnh cho cả hai vế.
.\scripts\verify.ps1

# Bỏ test khi đang viết code:
.\scripts\verify.ps1 -Skip test

# Chỉ chạy lint:
.\scripts\verify.ps1 -Only lint