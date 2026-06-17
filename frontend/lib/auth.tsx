interface JwtPayload {
  sub: string
  email: string
  name: string
  exp: number
  iat: number
}

export function getToken(): string | null {
  if (typeof window === 'undefined') {
    return null
  }
  return localStorage.getItem('token')
}

export function setToken(token: string): void {
  if (typeof window === 'undefined') {
    return
  }
  localStorage.setItem('token', token)
}

export function removeToken(): void {
  if (typeof window === 'undefined') {
    return
  }
  localStorage.removeItem('token')
}

export function isAuthenticated(): boolean {
  const token = getToken()
  if (!token) return false

  try {
    const payload = parseJwt(token)
    const currentTime = Math.floor(Date.now() / 1000)
    return payload.exp > currentTime
  } catch {
    return false
  }
}

export function getUser(): { id: string; email: string; name: string } | null {
  const token = getToken()
  if (!token) return null

  try {
    const payload = parseJwt(token)
    return {
      id: payload.sub,
      email: payload.email,
      name: payload.name
    }
  } catch {
    return null
  }
}

export function parseJwt(token: string): JwtPayload {
  const base64Url = token.split('.')[1]
  const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
  const jsonPayload = decodeURIComponent(
    atob(base64)
      .split('')
      .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
      .join('')
  )
  return JSON.parse(jsonPayload)
}