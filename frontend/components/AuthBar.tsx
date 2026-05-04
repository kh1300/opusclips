"use client";

import { FormEvent, useEffect, useState } from "react";
import { LogIn, LogOut, UserRound } from "lucide-react";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";

export function AuthBar() {
  const [session, setSession] = useState<Session | null>(null);
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!supabase) return;
    supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const {
      data: { subscription }
    } = supabase.auth.onAuthStateChange((_event, nextSession) => setSession(nextSession));
    return () => subscription.unsubscribe();
  }, []);

  async function signIn(event: FormEvent) {
    event.preventDefault();
    if (!supabase || !email) return;
    setMessage("");
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: window.location.origin + "/dashboard" }
    });
    setMessage(error ? error.message : "Check your email for the login link.");
  }

  if (!supabase) {
    return (
      <div className="inline-flex items-center gap-2 rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-300">
        <UserRound className="h-4 w-4 text-emerald-300" />
        Local dev session
      </div>
    );
  }

  if (session) {
    return (
      <div className="flex flex-wrap items-center gap-3">
        <div className="inline-flex items-center gap-2 rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-200">
          <UserRound className="h-4 w-4 text-emerald-300" />
          {session.user.email}
        </div>
        <button
          className="focus-ring inline-flex items-center gap-2 rounded-md border border-white/10 px-3 py-2 text-sm text-zinc-200 hover:bg-white/10"
          onClick={() => supabase.auth.signOut()}
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    );
  }

  return (
    <form className="flex flex-wrap items-center gap-2" onSubmit={signIn}>
      <input
        className="focus-ring h-10 min-w-64 rounded-md border border-white/10 bg-white/5 px-3 text-sm text-white placeholder:text-zinc-500"
        placeholder="Email"
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
      />
      <button className="focus-ring inline-flex h-10 items-center gap-2 rounded-md bg-emerald-300 px-4 text-sm font-semibold text-zinc-950 hover:bg-emerald-200">
        <LogIn className="h-4 w-4" />
        Sign in
      </button>
      {message ? <span className="basis-full text-sm text-zinc-400">{message}</span> : null}
    </form>
  );
}
