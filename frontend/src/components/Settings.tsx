import { useState } from 'react'
import { NGON_NGU, usePoiStore } from '../stores/poiStore'

export default function Settings() {
  const { lang, setLang } = usePoiStore()
  const [cheDoBanDo, setCheDoBanDo] = useState(localStorage.getItem('quan4-mapmode') ?? 'hybrid')
  const [riengTu, setRiengTu] = useState(localStorage.getItem('quan4-privacy') ?? 'co-ban')

  const doiBanDo = (cheDo: string) => {
    localStorage.setItem('quan4-mapmode', cheDo)
    setCheDoBanDo(cheDo)
  }
  const doiRiengTu = (muc: string) => {
    localStorage.setItem('quan4-privacy', muc)
    setRiengTu(muc)
  }

  return (
    <div>
      <h3 className="section-title">Cài đặt</h3>

      <div className="card">
        <div className="field">
          <span className="field__label">Ngôn ngữ</span>
          <div className="row">
            {NGON_NGU.map((n) => (
              <button key={n.ma} type="button" className={`btn btn--sm${n.ma === lang ? ' btn--primary' : ''}`} disabled={n.ma === lang} onClick={() => setLang(n.ma)}>
                {n.ten}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="field">
          <span className="field__label">Bản đồ: {cheDoBanDo}</span>
          <div className="row">
            {['cloud', 'offline', 'hybrid'].map((c) => (
              <button key={c} type="button" className={`btn btn--sm${c === cheDoBanDo ? ' btn--primary' : ''}`} disabled={c === cheDoBanDo} onClick={() => doiBanDo(c)}>
                {c}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="field">
          <span className="field__label">Riêng tư: {riengTu}</span>
          <div className="row">
            {['co-ban', 'khong-theo-doi'].map((m) => (
              <button key={m} type="button" className={`btn btn--sm${m === riengTu ? ' btn--primary' : ''}`} disabled={m === riengTu} onClick={() => doiRiengTu(m)}>
                {m}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
