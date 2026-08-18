// import { useEffect } from 'react';
// import { useRouter } from 'next/router';

// export default function AuthCallback() {
//   const router = useRouter();

//   useEffect(() => {
//     const hash = window.location.hash.substring(1);
//     const params = new URLSearchParams(hash);
//     const accessToken = params.get('access_token');
//     const refreshToken = params.get('refresh_token');

//     if (accessToken) {
//       localStorage.setItem('access_token', accessToken);
//       localStorage.setItem('refresh_token', refreshToken || '');
//       router.push('/dashboard');
//     } else {
//       router.push('/login');
//     }
//   }, []);

//   return <div>Signing you in...</div>;
// }