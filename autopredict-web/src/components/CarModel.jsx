import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stage, useGLTF } from '@react-three/drei';

const MODEL_PATH = '/car1.glb';

/* ── Local car GLB model ────────────────────────────── */
const Car = ({ scale = 5 }) => {
  const { scene } = useGLTF(MODEL_PATH);
  return (
    <group scale={scale} position={[0, 0, 0]}>
      <primitive object={scene} />
    </group>
  );
};

// Pre-load so the .glb starts downloading immediately
useGLTF.preload(MODEL_PATH);

/* ── Loading spinner shown while Suspense resolves ──── */
const Loader = () => (
  <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
    <div className="w-10 h-10 border-4 border-gray-300 rounded-full border-t-gray-900 animate-spin" />
    <span className="text-sm font-medium text-gray-400">Loading 3D model…</span>
  </div>
);

/* ── Main exported component ────────────────────────── */
const CarModel = () => {
  return (
    <div className="relative w-full h-full">
      <Loader />

      <Canvas
        style={{ background: 'transparent' }}
        gl={{ alpha: true, antialias: true }}
        camera={{ position: [4, 2.5, 4], fov: 50 }}
      >
        <Suspense fallback={null}>
          <Stage
            preset="rembrandt"
            intensity={0.6}
            environment="city"
            adjustCamera={1}
          >
            <Car />
          </Stage>
        </Suspense>

        <OrbitControls
          enableZoom={true}
          autoRotate
          autoRotateSpeed={0.8}
          minPolarAngle={Math.PI / 3}
          maxPolarAngle={Math.PI / 2.2}

        />
      </Canvas>
    </div>
  );
};

export default CarModel;
