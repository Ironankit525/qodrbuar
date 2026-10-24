import { useEffect, useState } from 'react'
import { getJson } from './api'

/** Fetches `path` (re-fetching when it changes). Keeps the previous data visible while loading. */
export function useApi(path) {
  const [state, setState] = useState({})

  useEffect(() => {
    let stale = false
    getJson(path).then(
      (data) => !stale && setState({ data }),
      (error) => !stale && setState({ error: error.message }),
    )
    return () => {
      stale = true
    }
  }, [path])

  return { ...state, loading: !state.data && !state.error }
}
