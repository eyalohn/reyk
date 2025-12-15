import Hero from '@/components/landing/hero';

export const metadata = {
  title: 'PyIsolate',
  description:
    'Ship Python libraries without dependency fear. PyIsolate enables seamless packaging of Python applications with all their dependencies isolated, ensuring consistent and reliable deployments across different environments.',
};

export default async function HomePage() {
  return (
    <div>
      <Hero />
    </div>
  );
}
