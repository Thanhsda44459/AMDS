import { useEffect, useState } from 'react'
import { thamDoBackend } from './offline/net'
import { usePoiStore } from './stores/poiStore'
import { useUiBundle } from './i18n/bundles'

const API_GOC = 'http://127.0.0.1:8000'

// Điều phối khởi động: tách readiness nội dung và UI bundle (REF-5).
// FE-004: tiếng Anh khởi động nhanh, đích đến khi cả hai làn sẵn sàng.
export function useStartup() {
  const { pois, loading, lang, fetchPOIs } = usePoiStore()
  const { sanSang: uiSanSang } = useUiBundle(lang === 'vi' ? 'en' : lang)
  const [mangSanSang, setMangSanSang] = useState(false)

  useEffect(() => {
    void fetchPOIs()
    void thamDoBackend(API_GOC).then(setMangSanSang)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const noiDungSanSang = !loading && pois.length > 0
  const hoanTat = noiDungSanSang && uiSanSang
  return { hoanTat, noiDungSanSang, uiSanSang, mangSanSang }
}
