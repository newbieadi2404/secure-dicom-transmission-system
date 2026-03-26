import { useEffect } from "react";

type Props = {
  email: string;
  setEmail: (value: string) => void;
};

export default function EmailInput({ email, setEmail }: Props) {
  // load saved email
  useEffect(() => {
    const saved = localStorage.getItem("email");
    if (saved) setEmail(saved);
  }, [setEmail]);

  // persist email even when cleared
  useEffect(() => {
    localStorage.setItem("email", email || "");
  }, [email]);

  return (
    <input
      type="email"
      className="px-4 py-2 rounded bg-gray-800 border border-gray-600 outline-none w-72 focus:ring-2 focus:ring-blue-500"
      placeholder="Enter email"
      value={email}
      onChange={(e) => setEmail(e.target.value)}
    />
  );
}