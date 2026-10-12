import { useEffect, useState } from 'react'
import { api, apiText } from './api'
import AnalyticsPanel from './AnalyticsPanel'
import AudioTasks from './AudioTasks'
import OwnerApprovals from './OwnerApprovals'
import type { Poi } from '../stores/poiStore'

const TRONG: Poi = { id: '', name: '', description: '', lat: 10.7569, lng: 106.7641, trigger_radius: 30, audio_priority: 0, lang: 'vi', is_fallback: false, audio_url: null }

// Hai cổng dùng chung MỘT cookie phiên, nên phiên chủ quán có thể "tràn" sang
// tab Admin khi đổi tab: `/admin/auth/me` trả 200 cho mọi phiên đã đăng nhập
// (hợp đồng class A) nên client phải tự chặn phiên cổng khách khỏi render
// giao diện quản trị. Quyền thật vẫn do server giữ (test ma trận quyền) —
// đây chỉ là chặn hiển thị, không phải phân quyền.
const CONG_KHACH = new Set(['poi_owner', 'user'])

export default function AdminApp({ onPoisChanged }: { onPoisChanged: () => void }) {
  const [user, setUser] = useState<string | null>(null)
  const [ten, setTen] = useState('')
  const [matKhau, setMatKhau] = useState('')
  const [loi, setLoi] = useState('')
  const [pois, setPois] = useState<Poi[]>([])
  const [form, setForm] = useState<Poi>(TRONG)
  const [dangSua, setDangSua] = useState(false)

  const taiPois = async () => setPois(await api<Poi[]>('/poi'))

  useEffect(() => {
    api<{ username: string; role: string }>('/admin/auth/me')
      .then((me) => {
        if (CONG_KHACH.has(me.role)) return
        setUser(me.username)
        void taiPois()
      })
      .catch(() => {})
  }, [])

  const dangNhap = async () => {
    setLoi('')
    const res = await apiText('/admin/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: ten, password: matKhau }),
    })
    if (!res.ok) {
      setLoi('Sai tên đăng nhập hoặc mật khẩu')
      return
    }
    const me = (await res.json()) as { username: string; role: string }
    if (CONG_KHACH.has(me.role)) {
      setLoi('Tài khoản này là chủ quán, không mở được cổng quản trị')
      return
    }
    setUser(me.username)
    setMatKhau('')
    await taiPois()
  }

  const dangXuat = async () => {
    await apiText('/admin/auth/logout', { method: 'POST' })
    setUser(null)
    setPois([])
  }

  const luu = async () => {
    setLoi('')
    try {
      if (dangSua) {
        await api(`/admin/pois/${form.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...form, id: undefined }),
        })
      } else {
        await api('/admin/pois', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...form, id: undefined }),
        })
      }
      setForm(TRONG)
      setDangSua(false)
      await taiPois()
      onPoisChanged()
    } catch {
      setLoi('Lưu thất bại, kiểm tra lat/lng và bán kính 5-200m')
    }
  }

  const xoa = async (id: string) => {
    if (!window.confirm('Xóa quán này?')) return
    await api(`/admin/pois/${id}`, { method: 'DELETE' })
    await taiPois()
    onPoisChanged()
  }

  if (user === null) {
    return (
      <div className="card">
        <h2 className="card__title">Đăng nhập admin</h2>
        <div className="field">
          <input className="input" placeholder="Tên đăng nhập" value={ten} onChange={(e) => setTen(e.target.value)} />
        </div>
        <div className="field">
          <input className="input" placeholder="Mật khẩu" type="password" value={matKhau} onChange={(e) => setMatKhau(e.target.value)} />
        </div>
        <button className="btn btn--primary" type="button" onClick={() => void dangNhap()}>
          Đăng nhập
        </button>
        {loi !== '' && <div className="notice notice--error mt">{loi}</div>}
      </div>
    )
  }

  return (
    <div>
      <div className="card">
        <div className="spread">
          <p>Xin chào <strong>{user}</strong></p>
          <button className="btn btn--sm" type="button" onClick={() => void dangXuat()}>Đăng xuất</button>
        </div>
      </div>

      <div className="card">
        <h3 className="card__title">{dangSua ? 'Sửa quán' : 'Thêm quán'}</h3>
        <div className="field">
          <input className="input" placeholder="Tên" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div className="field">
          <input className="input" placeholder="Mô tả" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </div>
        <div className="row">
          <div className="field" style={{ flex: 1 }}>
            <input className="input" placeholder="Lat" type="number" value={form.lat} onChange={(e) => setForm({ ...form, lat: Number(e.target.value) })} />
          </div>
          <div className="field" style={{ flex: 1 }}>
            <input className="input" placeholder="Lng" type="number" value={form.lng} onChange={(e) => setForm({ ...form, lng: Number(e.target.value) })} />
          </div>
        </div>
        <div className="field">
          <input className="input" placeholder="Bán kính" type="number" value={form.trigger_radius} onChange={(e) => setForm({ ...form, trigger_radius: Number(e.target.value) })} />
        </div>
        <div className="row">
          <button className="btn btn--primary" type="button" onClick={() => void luu()}>
            Lưu
          </button>
          {dangSua && (
            <button className="btn" type="button" onClick={() => { setForm(TRONG); setDangSua(false) }}>
              Hủy
            </button>
          )}
        </div>
        {loi !== '' && <div className="notice notice--error mt">{loi}</div>}
      </div>

      <div className="card">
        <table className="table">
          <tbody>
            {pois.map((p) => (
              <tr key={p.id}>
                <td>{p.name}</td>
                <td style={{ textAlign: 'right' }}>
                  <button className="btn btn--sm" type="button" onClick={() => { setForm(p); setDangSua(true) }}>
                    Sửa
                  </button>{' '}
                  <button className="btn btn--sm btn--danger" type="button" onClick={() => void xoa(p.id)}>
                    Xóa
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <OwnerApprovals />

      <AudioTasks />

      <AnalyticsPanel />
    </div>
  )
}
