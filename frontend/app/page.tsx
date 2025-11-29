"use client";

import { useState } from 'react';
import axios, { isAxiosError } from 'axios';
// Ya no necesitamos importar MercadoPagoButton.

export default function Home() {
  // Almacenamos la URL de pago. Si está llena, mostramos el enlace de redirección.
  const [paymentUrl, setPaymentUrl] = useState<string | null>(null); 
  const [isLoading, setIsLoading] = useState(false);

  const handleBooking = async () => {
    setIsLoading(true);
    
    // Usamos una fecha en el futuro que sea válida (30 de diciembre)
    const start_time = "2025-12-30T19:00:00"; 
    const end_time = "2025-12-30T20:00:00";

    try {
      console.log("Enviando reserva:", start_time, "a", end_time);
      
      const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/reservations/`, {
        court: 1,
        start_time: start_time, 
        end_time: end_time,
      });

      console.log("Respuesta Backend:", response.data);
      
      const { payment_url } = response.data;
      
      if (payment_url) {
        // Redirigir al usuario al link de pago de Mercado Pago
        window.location.href = payment_url; 
        
        // No llamamos a setPaymentUrl si redirigimos inmediatamente, pero
        // si lo hacemos para mantener la visibilidad en el código, no hay problema.
        setPaymentUrl(payment_url); 
        
      } else {
        // El backend respondió 201 pero no devolvió el link (error en services.py)
        throw new Error("El Backend no generó la URL de pago (Revisar logs de Django).");
      }
      
    } catch (error) {
      console.error("Error completo:", error);
      
      if (isAxiosError(error)) {
        if (error.response) {
            // Mostrar error de validación o conflicto (400, 409)
            alert(`Error del Servidor (${error.response.status}): ${JSON.stringify(error.response.data)}`);
        } else {
             // Error de red (CORS o Django apagado)
             alert("Error de Red: No hubo respuesta. Revisa CORS en Django o que el servidor esté prendido.");
        }
      } else if (error instanceof Error) {
          alert(`Error de configuración: ${error.message}`);
      }
      
    } finally {
      // Dejamos el finally para que se desactive el loading si algo falla
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md text-center max-w-lg w-full">
        <h1 className="text-2xl font-bold mb-4 text-gray-800">Reserva tu Cancha</h1>
        
        <p className="mb-6 text-gray-600">
          Cancha 1 - Fútbol 5 <br />
          Precio estimado: S/ 80.00
        </p>

        {/* El botón ahora redirige directamente al URL de pago */}
        <button
          onClick={handleBooking}
          disabled={isLoading}
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded w-full transition-colors disabled:bg-gray-400"
        >
          {isLoading ? "Redirigiendo a Pasarela..." : "Confirmar y Pagar"}
        </button>
        
        {/* Este bloque es solo para debug en caso de que la redirección no sea instantánea */}
        {paymentUrl && (
          <div className="p-4 bg-yellow-100 border border-yellow-300 rounded-lg mt-4">
            <p className="text-sm text-yellow-700 font-semibold mb-3">
              Si no redirige automáticamente, haz clic aquí:
            </p>
            <a 
              href={paymentUrl} 
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block bg-green-500 text-white font-bold py-2 px-4 rounded w-full hover:bg-green-600 transition"
            >
              Pagar con Mercado Pago (Sandbox)
            </a>
          </div>
        )}
      </div>
    </main>
  );
}