import { useEffect, useState } from 'react'
import { api, apiText } from './api'

interface Task {
  task_id: string
  poi_id: string
  lang: string
  status: string
  progress: number
}

export default function AudioTasks() {
  const [tasks, setTasks] = useState<Task[]>([])

  const tai = async () => setTasks(await api<Task[]>('/audio/tasks'))

  useEffect(() => {
    api<Task[]>('/audio/tasks')
      .then(setTasks)
      .catch(() => {})
    const nguon = new EventSource('http://127.0.0.1:8000/audio/tasks/stream', { withCredentials: true })
    nguon.onmessage = () => void tai()
    nguon.onerror = () => nguon.close()
    return () => nguon.close()
  }, [])

  const lenh = async (id: string, l: string) => {
    await apiText(`/audio/tasks/${id}/${l}`, { method: 'POST' })
    await tai()
  }

  return (
    <div className="card">
      <h3 className="card__title">Tác vụ audio</h3>
      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {tasks.map((t) => (
          <li key={t.task_id} style={{ padding: '10px 0', borderBottom: '1px solid var(--amds-border)' }}>
            <div className="spread">
              <span>
                <strong>{t.poi_id}</strong> <span className="muted">[{t.lang}]</span>{' '}
                <span className={`badge badge--${t.status === 'done' ? 'ok' : t.status === 'error' ? 'error' : 'warn'}`}>{t.status} {t.progress}%</span>
              </span>
              <span className="row">
                <button className="btn btn--sm" type="button" onClick={() => void lenh(t.task_id, 'pause')}>Dừng</button>
                <button className="btn btn--sm" type="button" onClick={() => void lenh(t.task_id, 'resume')}>Tiếp</button>
                <button className="btn btn--sm btn--danger" type="button" onClick={() => void lenh(t.task_id, 'cancel')}>Hủy</button>
              </span>
            </div>
            <div className="progress mt">
              <div className="progress__bar" style={{ width: `${t.progress}%` }} />
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
