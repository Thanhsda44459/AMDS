import { useEffect, useState } from 'react'
import { api, apiText } from './api'

interface DonDangKy {
  username: string
  status: string
}

interface SubmissionChoDuyet {
  id: string
  username: string
  name: string
  created_at: string | null
}

// Chủ quán đăng ký ở portal Owner; admin duyệt ở đây thì họ mới gửi được quán.
// Hai hàng đợi vì một chủ quán phải qua hai cổng: duyệt tài khoản, rồi duyệt
// từng quán. Thiếu một trong hai thì vòng lặp "gửi → thông báo" không đóng.
export default function OwnerApprovals() {
  const [don, setDon] = useState<DonDangKy[]>([])
  const [choDuyet, setChoDuyet] = useState<SubmissionChoDuyet[]>([])
  const [ghiChu, setGhiChu] = useState<Record<string, string>>({})
  const [loi, setLoi] = useState('')

  const tai = async () => {
    try {
      setDon(await api<DonDangKy[]>('/owner/registrations'))
      setChoDuyet(await api<SubmissionChoDuyet[]>('/owner/submissions/pending'))
      setLoi('')
    } catch {
      setLoi('Không xem được danh sách duyệt (cần quyền user:update và poi:approve)')
    }
  }

  // Vào trang phải tải CẢ HAI hàng đợi: chỉ tải danh đăng ký thì hàng quán chờ
  // duyệt trống cho tới lần duyệt đầu, mà E2E kiểm đúng ô này.
  useEffect(() => {
    api<DonDangKy[]>('/owner/registrations')
      .then(setDon)
      .catch(() => setLoi('Không xem được danh sách đăng ký (cần quyền user:update)'))
    api<SubmissionChoDuyet[]>('/owner/submissions/pending')
      .then(setChoDuyet)
      .catch(() => setLoi('Không xem được danh sách quán chờ duyệt (cần quyền poi:approve)'))
  }, [])

  const duyetTaiKhoan = async (ten: string) => {
    await apiText(`/owner/registrations/${ten}/approve`, { method: 'POST' })
    await tai()
  }

  const tuChoi = async (ten: string) => {
    const note = (ghiChu[ten] ?? '').trim()
    if (note === '') {
      setLoi('Từ chối phải có ghi chú để chủ quán biết cần bổ sung gì')
      return
    }
    const res = await apiText(`/owner/registrations/${ten}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ admin_note: note }),
    })
    if (!res.ok) {
      setLoi('Từ chối thất bại')
      return
    }
    await tai()
  }

  // Duyệt quán sẽ tạo POI và bắn thông báo cho chủ quán — đúng mốc mà E2E kiểm.
  const duyetQuan = async (id: string) => {
    const res = await apiText(`/owner/submissions/${id}/approve`, { method: 'POST' })
    if (!res.ok) {
      setLoi('Duyệt quán thất bại')
      return
    }
    await tai()
  }

  return (
    <div className="card">
      <h3 className="card__title">Kiểm duyệt chủ quán</h3>

      <h4 className="card__subtitle">Đơn đăng ký ({don.length})</h4>
      {don.length === 0 ? (
        <p className="muted">Không có đơn chờ duyệt.</p>
      ) : (
        <table className="table">
          <tbody>
            {don.map((d) => (
              <tr key={d.username}>
                <td>
                  <strong>{d.username}</strong>
                  <div className="field">
                    <input
                      className="input"
                      placeholder="Ghi chú khi từ chối"
                      value={ghiChu[d.username] ?? ''}
                      onChange={(e) => setGhiChu({ ...ghiChu, [d.username]: e.target.value })}
                    />
                  </div>
                </td>
                <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                  <button
                    className="btn btn--sm btn--primary"
                    type="button"
                    onClick={() => void duyetTaiKhoan(d.username)}
                  >
                    Duyệt
                  </button>{' '}
                  <button
                    className="btn btn--sm btn--danger"
                    type="button"
                    onClick={() => void tuChoi(d.username)}
                  >
                    Từ chối
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h4 className="card__subtitle" style={{ marginTop: 16 }}>
        Quán chờ duyệt ({choDuyet.length})
      </h4>
      {choDuyet.length === 0 ? (
        <p className="muted">Không có quán chờ duyệt.</p>
      ) : (
        <table className="table">
          <tbody>
            {choDuyet.map((s) => (
              <tr key={s.id}>
                <td>
                  <strong>{s.name}</strong>
                  <div className="muted" style={{ fontSize: '0.82rem' }}>
                    gửi bởi {s.username}
                  </div>
                </td>
                <td style={{ textAlign: 'right' }}>
                  <button
                    className="btn btn--sm btn--primary"
                    type="button"
                    onClick={() => void duyetQuan(s.id)}
                  >
                    Duyệt quán
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {loi !== '' && <div className="notice notice--error mt">{loi}</div>}
    </div>
  )
}