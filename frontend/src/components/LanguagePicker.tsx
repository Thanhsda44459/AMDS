import { NGON_NGU, usePoiStore } from '../stores/poiStore'

export default function LanguagePicker() {
  const { lang, setLang, pois } = usePoiStore()
  const duPhong = pois.some((p) => p.is_fallback)
  return (
    <div className="mb">
      <div className="row" role="group" aria-label="Chọn ngôn ngữ">
        {NGON_NGU.map((n) => (
          <button
            key={n.ma}
            type="button"
            className={`btn btn--sm${n.ma === lang ? ' btn--primary' : ''}`}
            disabled={n.ma === lang}
            onClick={() => setLang(n.ma)}
          >
            {n.ten}
          </button>
        ))}
      </div>
      {duPhong && <p className="muted" style={{ fontSize: '0.82rem', marginTop: 6 }}>Đang hiện bản dự phòng cho ngôn ngữ này.</p>}
    </div>
  )
}
