import React from "react";

const AuthLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div 
      className="flex items-center justify-start min-h-screen bg-cover bg-center bg-no-repeat relative"
      style={{ backgroundImage: "url('/back.png')" }}
    >
      {/* Content shifted 15% from the right edge in RTL */}
      <div className="relative z-10 w-full pr-[5%] md:pr-[15%] flex justify-start">
        {children}
      </div>
    </div>
  );
};

export default AuthLayout;
