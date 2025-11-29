// src/components/MercadoPagoButton.tsx
"use client";

import { initMercadoPago, Wallet } from '@mercadopago/sdk-react';
import { useEffect } from 'react'; // <--- Lo necesitamos ahora

interface Props {
  preferenceId: string;
}

// 1. Usamos una constante para la clave pública
const PUBLIC_KEY = process.env.NEXT_PUBLIC_MP_PUBLIC_KEY;

export default function MercadoPagoButton({ preferenceId }: Props) {
  
  // 2. Inicializamos el SDK dentro de useEffect para asegurar el ciclo de vida
  useEffect(() => {
    if (PUBLIC_KEY) {
      console.log("✅ MP: Inicializando SDK con clave:", PUBLIC_KEY.substring(0, 10) + '...');
      initMercadoPago(PUBLIC_KEY);
    } else {
      console.error("❌ MP: Error FATAL. La clave pública no fue cargada.");
    }
  }, []); // El array vacío [] asegura que se ejecute una sola vez al montar

  if (!preferenceId) return null;

  return (
    <div className="w-full max-w-md mx-auto mt-4">
      {/* 3. Renderizamos Wallet solo si la clave existe para evitar errores */}
      {PUBLIC_KEY ? (
        <Wallet initialization={{ preferenceId: preferenceId }} />
      ) : (
        <p className="text-red-600 text-sm">Error de configuración de Public Key. Revise .env.local</p>
      )}
    </div>
  );
}