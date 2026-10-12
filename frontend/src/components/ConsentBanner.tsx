import { useConsentStore } from '../stores/consentStore'
import { thuHoiDongY, xinDongY } from '../analytics/service'

// ANA-001 + UI-002: hỏi rõ ràng, cho cả hai lựa chọn, nhớ lựa chọn.
// "Từ chối" phải dễ bấm bằng "Đồng ý" — không tính giá trị của việc đồng ý.
export default function ConsentBanner() {
  const trangThai = useConsentStore((s) => s.trangThai)
  const tracked = useConsentStore((s) => s.trackedOnlineUsers)

  if (trangThai !== 'chua-chon') {
    return (
      <div className="card">
        <div className="spread">
          <span className="muted">
            Chia sẻ dữ liệu ẩn danh: <strong>{trangThai === 'granted' ? 'đang bật' : 'đang tắt'}</strong>
            {trangThai === 'granted' && tracked !== null && ` · ${tracked} thiết bị đang dùng`}
          </span>
          {trangThai === 'granted' && (
            <button className="btn btn--sm" type="button" onClick={() => void thuHoiDongY()}>
              Tắt thu thập
            </button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="card" role="dialog" aria-label="Xin phép chia sẻ dữ liệu ẩn danh">
      <h3 className="card__title">Chia sẻ dữ liệu ẩn danh?</h3>
      <p className="card__subtitle">
        Chỉ gom số lượt xem, lượt nghe và cụm từ tìm kiếm. Không ghi tên, không ghi tài khoản, không ghi vị trí
        của bạn vào phần này. Bạn tắt bất cứ lúc nào.
      </p>
      <div className="row">
        <button className="btn btn--primary" type="button" onClick={() => void xinDongY()}>
          Cho phép
        </button>
        <button className="btn btn--ghost" type="button" onClick={() => void thuHoiDongY()}>
          Không cho phép
        </button>
      </div>
    </div>
  )
}