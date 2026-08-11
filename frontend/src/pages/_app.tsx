import type { AppProps } from 'next/app';
import { AppStateProvider } from '../context/AppStateContext';
import '../styles/globals.css';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <AppStateProvider>
      <Component {...pageProps} />
    </AppStateProvider>
  );
}
