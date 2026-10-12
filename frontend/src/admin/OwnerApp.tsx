import { useState } from 'react'
import { api, apiText } from './api'

export default function OwnerApp() {
  const [user, setUser] = useState<string | null>(null)
  const [ten, setTen] = useState('')
  const [matKhau, setMatKhau] = useState('')
  const [cccd, setCccd] = useState('')
  const [loi, setLoi] = useState('')
  const [trangThai, setTrangThai] = useState('')
  const [tenQuan, setTenQuan] = useState('')
  const [moTa, setMoTa] = useState('')
  const [thongBao, setThongBao] = useState<{ id: string; message: string; read: boolean }[]>([])

  const dangNhap = async () => {
    const res = await apiText('/admin/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: ten, password: matKhau }),
    })
    if (!res.ok) {
      setLoi('Sai tên đăng nhập hoặc mật khẩu')
      return
    }
    setUser(ten)
    setMatKhau('')
    try {
      const st = await api<{ status: string }>('/owner/registration-status')
      setTrangThai(st.status)
    } catch {
      // 404 ở đây nghĩa là tài khoản không đăng ký chủ quán, tức admin.
      setTrangThai('admin')
      return
    }
    // Tách riêng vì chủ quán chưa duyệt bị 403 ở endpoint thông báo; nếu để
    // chung try thì lỗi này sẽ ghi đè trạng thái thật thành "admin" và giao
    // diện hiện sai (mất cảnh báo chờ duyệt lẫn ô gửi quán).
    setThongBao(await api<{ id: string; message: string; read: boolean }[]>('/owner/notifications').catch(() => []))
  }

  const dangKy = async () => {
    const res = await apiText('/owner/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: ten, password: matKhau, cccd }),
    })
    setLoi(res.ok ? '' : 'Đăng ký thất bại (trùng tên hoặc thiếu CCCD)')
    if (res.ok) setTrangThai('pending')
  }

  const guiQuan = async (dungAI: boolean) => {
    let moTaGui = moTa
    if (dungAI) {
      try {
        const goi = await api<{ text: string }>('/ai/enhance-description', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: moTa }),
        })
        moTaGui = goi.text
        setMoTa(goi.text)
      } catch {
        setLoi('AI bận hoặc hết lượt hôm nay')
        return
      }
    }
    await api('/owner/submissions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: tenQuan, description: moTaGui, lat: 10.7569, lng: 106.7641 }),
    })
    setTenQuan('')
    setMoTa('')
  }

  if (user === null) {
    return (
      <div className="card">
        <h2 className="card__title">Chủ quán</h2>
        <div className="field">
          <input className="input" placeholder="Tên đăng nhập" value={ten} onChange={(e) => setTen(e.target.value)} />
        </div>
        <div className="field">
          <input className="input" placeholder="Mật khẩu" type="password" value={matKhau} onChange={(e) => setMatKhau(e.target.value)} />
        </div>
        <div className="field">
          <input className="input" placeholder="CCCD" value={cccd} onChange={(e) => setCccd(e.target.value)} />
        </div>
        <div className="row">
          <button className="btn btn--primary" type="button" onClick={() => void dangNhap()}>Đăng nhập</button>
          <button className="btn btn--accent" type="button" onClick={() => void dangKy()}>Đăng ký chủ quán</button>
        </div>
        {loi !== '' && <div className="notice notice--error mt">{loi}</div>}
      </div>
    )
  }

  return (
    <div>
      <div className="card">
        <div className="spread">
          <p>Xin chào <strong>{user}</strong></p>
          <span className="badge badge--accent">{trangThai}</span>
        </div>
      </div>

      {trangThai !== 'approved' && trangThai !== 'admin' && (
        <div className="notice notice--warn">Tài khoản chờ duyệt, chưa gửi được quán.</div>
      )}

      <div className="card">
        <h3 className="card__title">Gửi quán mới</h3>
        <div className="field">
          <input className="input" placeholder="Tên quán" value={tenQuan} onChange={(e) => setTenQuan(e.target.value)} />
        </div>
        <div className="field">
          <input className="input" placeholder="Mô tả" value={moTa} onChange={(e) => setMoTa(e.target.value)} />
        </div>
        <div className="row">
          <button className="btn btn--primary" type="button" onClick={() => void guiQuan(false)}>Gửi</button>
          <button className="btn btn--accent" type="button" onClick={() => void guiQuan(true)}>AI viết lại rồi gửi</button>
        </div>
        {loi !== '' && <div className="notice notice--error mt">{loi}</div>}
      </div>

      <div className="card">
        <h3 className="card__title">Thông báo</h3>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {thongBao.map((t) => (
            <li key={t.id} style={{ padding: '8px 0', borderBottom: '1px solid var(--amds-border)' }}>
              {!t.read && <span className="badge badge--error" style={{ marginRight: 8 }}>Mới</span>}
              {t.message}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
