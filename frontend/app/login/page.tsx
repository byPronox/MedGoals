'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import styles from './login.module.css';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const router = useRouter();

  const onLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      const res = await fetch('/api/session/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok || data?.status !== 'ok') throw new Error(data?.message || 'Login failed');
      router.replace('/portal');
    } catch (error: any) {
      setErr(error.message || String(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.cardWrapper}>
        <div className={styles.card}>
          <div>
            <h1 className={styles.title}>MED GOALS</h1>
            <p className={styles.subtitle}>
              Enter your assigned credentials to manage your team goals.
            </p>
          </div>
          <form onSubmit={onLogin} className={styles.form}>
            <div className={styles.field}>
              <label htmlFor="email" className={styles.label}>
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@email.com"
                required
                className={styles.input}
              />
            </div>

            <div className={styles.field}>
              <label htmlFor="password" className={styles.label}>
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="********"
                required
                className={styles.input}
              />
            </div>

            <div className={styles.actions}>
              <button type="submit" disabled={loading} className={styles.submit}>
                {loading ? 'Connecting…' : 'Sign in'}
              </button>
            </div>
          </form>

          {err && <p className={styles.error}>{err}</p>}
        </div>
      </div>
    </div>
  );
}
