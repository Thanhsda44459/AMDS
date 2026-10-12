import { useEffect, useState } from 'react'
import { type PackHook } from './useMapPack'

const API_GOC = 'http://127.0.0.1:8000'

interface TepAudio {
  url: string
  sha256: string
  bytes: number
}

export default function OfflinePacks({ pack }: { pack: PackHook }) {
  const { cheDo, setCheDo, trangThai, taiPack } = pack
  const [scopes, setScopes] = useState<string[]>([])
  const [langPack, setLangPack] = useState('')
  const [thatBaiLienTiep, setThatBaiLienTiep] = useState(0)

  useEffect(() => {
    fetch(`${API_GOC}/maps/offline-options`)
      .then((r) => r.json())
      .then((d: { scopes: string[] }) => {
        setScopes(d.scopes)
        setThatBaiLienTiep(0)
      })
      .catch(() => setThatBaiLienTiep((n) => n + 1))
  }, [])

  const taiAudioPack = async (lang: string) => {
    const man = (await fetch(`${API_GOC}/maps/audio-pack?lang=${lang}`).then((r) => r.json())) as { files: TepAudio[] }
    const cache = await caches.open(`audio-pack-${lang}`)
    for (const tep of man.files) {
      const res = await fetch(`${API_GOC}${tep.url.split('?')[0]}?l=${lang}`)
      await cache.put(`${API_GOC}${tep.url}`, res.clone())
    }
    setLangPack(lang)
  }

  return (
    <div>
      <h3 className="section-title">Gói offline</h3>

      <div className="card">
        <div className="field">
          <span className="field__label">Chế độ bản đồ: {cheDo}</span>
          <div className="row">
            {(['cloud', 'offline', 'hybrid'] as const).map((c) => (
              <button key={c} type="button" className={`btn btn--sm${c === cheDo ? ' btn--primary' : ''}`} onClick={() => setCheDo(c)}>
                {c}
              </button>
            ))}
          </div>
        </div>
      </div>

      {thatBaiLienTiep >= 3 && <div className="notice notice--error">Manifest lỗi liên tiếp, nghỉ một lúc rồi thử lại</div>}

      <div className="card">
        <p className="card__subtitle">Gói bản đồ</p>
        {scopes.map((s) => (
          <div key={s} className="row" style={{ marginBottom: 8 }}>
            <span style={{ flex: 1 }}>{s}</span>
            <button className="btn btn--sm btn--primary" type="button" onClick={() => void taiPack(s)}>
              Cài pack
            </button>
            <button className="btn btn--sm" type="button" onClick={() => void taiPack(s, true)}>
              Cài đè (replace)
            </button>
          </div>
        ))}
        {trangThai !== '' && <p className="muted" style={{ fontSize: '0.82rem' }}>{trangThai}</p>}
      </div>

      <div className="card">
        <p className="card__subtitle">Gói audio</p>
        <div className="row">
          {['vi', 'en', 'zh', 'ja', 'ko'].map((l) => (
            <button key={l} type="button" className="btn btn--sm" onClick={() => void taiAudioPack(l)}>{l}</button>
          ))}
        </div>
        {langPack !== '' && <div className="badge badge--ok mt">Đã cài audio {langPack}</div>}
      </div>
    </div>
  )
}
