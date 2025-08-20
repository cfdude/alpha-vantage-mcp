import PostPage from '@/components/PostPage'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  icons: {
    icon: 'https://www.alphavantage.co/static/img/favicon.ico',
  },
}

export default function Home() {
  return <PostPage showToc={true} />
}