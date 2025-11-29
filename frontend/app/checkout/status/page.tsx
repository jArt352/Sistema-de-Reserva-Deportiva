"use client";

import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useEffect, useState, Suspense } from 'react';

// Creamos un componente interno para usar useSearchParams seguro
function StatusContent() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<string | null>(null);
  const [paymentId, setPaymentId] = useState<string | null>(null);

  useEffect(() => {
    // Mercado Pago agrega esto a la URL: ?status=approved&payment_id=123...
    setStatus(searchParams.get('status'));
    setPaymentId(searchParams.get('payment_id'));
  }, [searchParams]);

  return (
    <div className="bg-white p-8 rounded-xl shadow-lg max-w-md w-full text-center">
      {/* 1. PAGO APROBADO */}
      {status === 'approved' && (
        <>
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-10 h-10 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">¡Pago Exitoso!</h1>
          <p className="text-gray-600 mb-6">
            Tu reserva ha sido confirmada correctamente.<br/>
            <span className="text-sm text-gray-400">ID Pago: {paymentId}</span>
          </p>
        </>
      )}

      {/* 2. PAGO RECHAZADO */}
      {status === 'rejected' && (
        <>
          <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-10 h-10 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Pago Rechazado</h1>
          <p className="text-gray-600 mb-6">Hubo un problema con el método de pago.</p>
        </>
      )}

      {/* 3. PAGO PENDIENTE */}
      {status === 'pending' && (
        <>
          <div className="w-20 h-20 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-10 h-10 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Pago Pendiente</h1>
          <p className="text-gray-600 mb-6">Estamos procesando tu pago (Efectivo/Transferencia).</p>
        </>
      )}

      <Link href="/" className="block w-full bg-blue-600 text-white py-3 rounded-lg font-bold hover:bg-blue-700 transition">
        Volver al Inicio
      </Link>
    </div>
  );
}

// Página Principal exportada
export default function CheckoutStatusPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 bg-gray-50">
      <Suspense fallback={<p>Cargando estado...</p>}>
        <StatusContent />
      </Suspense>
    </main>
  );
}