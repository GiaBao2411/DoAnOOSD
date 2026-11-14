"""Hằng số trạng thái và giá trị liệt kê (mục 2.4 của báo cáo)."""

# Báo cáo sự cố
BC_MOI_GUI = "Mới gửi"
BC_DANG_XEM_XET = "Đang xem xét"
BC_CHO_BO_SUNG = "Chờ bổ sung"
BC_CHO_PHAN_CONG = "Chờ phân công"
BC_DA_PHAN_CONG = "Đã phân công"
BC_DANG_XU_LY = "Đang xử lý"
BC_CHO_NGHIEM_THU = "Chờ duyệt kết quả"
BC_CHO_CONG_KHAI = "Chờ công khai"
BC_HOAN_TAT = "Hoàn tất"
BC_BI_TU_CHOI = "Bị từ chối"
BC_DA_DONG = "Đã đóng"
BC_ALL = [BC_MOI_GUI, BC_DANG_XEM_XET, BC_CHO_BO_SUNG, BC_CHO_PHAN_CONG, BC_DA_PHAN_CONG, BC_DANG_XU_LY,
          BC_CHO_NGHIEM_THU, BC_CHO_CONG_KHAI, BC_HOAN_TAT, BC_BI_TU_CHOI, BC_DA_DONG]
BC_KET_THUC = [BC_HOAN_TAT, BC_BI_TU_CHOI, BC_DA_DONG]
# Các bước hiển thị trên thanh tiến trình cho người dân
LOC_O_DON_VI = "o-don-vi"  # bộ lọc tra cứu nội bộ: Đã phân công + Đang xử lý
BC_BUOC = [BC_MOI_GUI, BC_DANG_XEM_XET, BC_CHO_PHAN_CONG, BC_DA_PHAN_CONG, BC_DANG_XU_LY, BC_CHO_NGHIEM_THU,
           BC_CHO_CONG_KHAI, BC_HOAN_TAT]

# Chuyển trạng thái hợp lệ của báo cáo (biểu đồ trạng thái lớp BaoCaoSuCo)
BC_CHUYEN = {
    None: [BC_MOI_GUI],
    BC_MOI_GUI: [BC_DANG_XEM_XET],
    BC_DANG_XEM_XET: [BC_CHO_BO_SUNG, BC_BI_TU_CHOI, BC_CHO_PHAN_CONG],
    BC_CHO_BO_SUNG: [BC_DANG_XEM_XET, BC_DA_DONG],
    BC_CHO_PHAN_CONG: [BC_DA_PHAN_CONG],
    BC_DA_PHAN_CONG: [BC_CHO_PHAN_CONG, BC_DANG_XU_LY, BC_DA_PHAN_CONG],
    BC_DANG_XU_LY: [BC_CHO_NGHIEM_THU, BC_DA_PHAN_CONG],
    BC_CHO_NGHIEM_THU: [BC_DANG_XU_LY, BC_CHO_CONG_KHAI, BC_DA_DONG],
    BC_CHO_CONG_KHAI: [BC_HOAN_TAT],
    BC_HOAN_TAT: [], BC_BI_TU_CHOI: [], BC_DA_DONG: [],
}

UU_TIEN = ["Khẩn cấp", "Cao", "Trung bình", "Thấp"]

# Phân công
PC_CHO_TIEP_NHAN = "Chờ tiếp nhận"
PC_DANG_XU_LY = "Đang xử lý"
PC_CHO_NGHIEM_THU = "Chờ duyệt kết quả"
PC_HOAN_THANH = "Hoàn thành"
PC_BI_TRA_LAI = "Bị trả lại"
PC_DA_THAY_THE = "Đã thay thế"
PC_ALL = [PC_CHO_TIEP_NHAN, PC_DANG_XU_LY, PC_CHO_NGHIEM_THU, PC_HOAN_THANH, PC_BI_TRA_LAI, PC_DA_THAY_THE]
PC_HIEU_LUC = [PC_CHO_TIEP_NHAN, PC_DANG_XU_LY, PC_CHO_NGHIEM_THU]

# Yêu cầu bổ sung
YC_CHO = "Chờ phản hồi"
YC_DA_PHAN_HOI = "Đã phản hồi"
YC_QUA_HAN = "Quá hạn"
YC_ALL = [YC_CHO, YC_DA_PHAN_HOI, YC_QUA_HAN]

# Kiểm duyệt
KD_CHO_DUYET = "Chờ duyệt"
KD_DA_DUYET = "Đã duyệt"
KD_KHONG_DUYET = "Không duyệt"
KD_ALL = [KD_CHO_DUYET, KD_DA_DUYET, KD_KHONG_DUYET]

# Nghiệm thu
NT_DAT = "Đạt"
NT_CHUA_DAT = "Chưa đạt"
NT_KHONG_CO_SU_CO = "Không có sự cố"
NT_ALL = [NT_DAT, NT_CHUA_DAT, NT_KHONG_CO_SU_CO]

# Cập nhật xử lý
CN_GHI_NHAN = "Ghi nhận hiện trường"
CN_TIEN_DO = "Tiến độ"
CN_KET_QUA = "Kết quả"
CN_KHONG_SU_CO = "Không có sự cố"
CN_ALL = [CN_GHI_NHAN, CN_TIEN_DO, CN_KET_QUA, CN_KHONG_SU_CO]

GD_TRUOC = "Trước"
GD_SAU = "Sau"

# Tài khoản
TK_CAN_BO = "Cán bộ"
TK_DON_VI = "Đơn vị"
TK_HOAT_DONG = "Hoạt động"
TK_BI_KHOA = "Bị khóa"

# Tham số hệ thống (mã, giá trị mặc định, mô tả)
THAM_SO_MAC_DINH = [
    ("HAN_BO_SUNG_NGAY", "3", "Số ngày người dân được bổ sung thông tin"),
    ("SO_TEP_TOI_DA", "5", "Số tệp tối đa mỗi lần gửi"),
    ("ANH_TOI_DA_MB", "10", "Dung lượng tối đa một ảnh (MB)"),
    ("VIDEO_TOI_DA_MB", "50", "Dung lượng tối đa một video (MB)"),
    ("TRAM_MAT_KET_NOI_PHUT", "5", "Thiết bị đo không gửi số liệu quá số phút này thì coi là mất kết nối"),
]

# ---- Thiết bị đo IoT (module M8)
KHI_TOI_DA_PPM = 5000      # dải đo MQ135 (BR17)
TDS_TOI_DA_PPM = 3000      # dải đo cảm biến TDS (BR17)
NGUONG_MAC_DINH = 1000     # ngưỡng cảnh báo mặc định (BR18)
