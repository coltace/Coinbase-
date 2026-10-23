const SEPOLIA_CHAIN_ID = "0xaa36a7";
const LAST_TRANSFER_KEY = "coinpilot-last-transfer";
let csrfToken = null;
let currentUser = null;
let connectedAddress = null;

const $ = (id) => document.getElementById(id);
const authPanel = $("authPanel");
const appPanel = $("appPanel");

function message(id, text) { $(id).textContent = text; }

async function apiRequest(path, options = {}) {
  const method = options.method || "GET";
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method) && csrfToken) headers["X-CSRF-Token"] = csrfToken;
  const response = await fetch(path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed: ${response.status}`);
  if (data.csrfToken) csrfToken = data.csrfToken;
  return data;
}

function showTransactionLink(hash) {
  const link = $("transactionLink");
  if (!hash) { link.hidden = true; return; }
  link.href = `https://sepolia.etherscan.io/tx/${encodeURIComponent(hash)}`;
  link.hidden = false;
}

async function switchToSepolia() {
  if (!window.ethereum) throw new Error("MetaMask not detected.");
  try {
    await window.ethereum.request({ method: "wallet_switchEthereumChain", params: [{ chainId: SEPOLIA_CHAIN_ID }] });
  } catch (error) {
    if (error.code !== 4902) throw error;
    await window.ethereum.request({ method: "wallet_addEthereumChain", params: [{ chainId: SEPOLIA_CHAIN_ID, chainName: "Sepolia", nativeCurrency: { name: "Sepolia Ether", symbol: "ETH", decimals: 18 }, rpcUrls: ["https://rpc.sepolia.org"], blockExplorerUrls: ["https://sepolia.etherscan.io"] }] });
  }
}

async function connectWallet() {
  await switchToSepolia();
  const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
  if (!accounts.length) throw new Error("No account selected.");
  connectedAddress = accounts[0].toLowerCase();
  message("walletStatus", `Connected: ${connectedAddress}`);
  return connectedAddress;
}

function renderUser(user) {
  currentUser = user;
  authPanel.hidden = Boolean(user);
  appPanel.hidden = !user;
  if (!user) return;
  message("userStatus", `Signed in as ${user.email} (${user.role})`);
  $("adminPanel").hidden = user.role !== "admin";
  if (user.role === "admin") message("transferabilityText", "enforced by the configured PTC contract");
}

async function login() {
  const data = await apiRequest("/api/auth/login", { method: "POST", body: JSON.stringify({ email: $("email").value.trim(), password: $("password").value }) });
  renderUser(data.user);
  message("authStatus", "");
}

async function loadSession() {
  try {
    const data = await apiRequest("/api/auth/me");
    renderUser(data.user);
  } catch {
    try { const data = await apiRequest("/api/auth/csrf"); csrfToken = data.csrfToken; } catch {}
  }
}

async function verifyEthTransfer(intentId, txHash) {
  const data = await apiRequest(`/api/transfers/${encodeURIComponent(intentId)}/verify`, { method: "POST", body: JSON.stringify({ txHash }) });
  message("transferStatus", `Transfer status: ${data.status}${data.message ? ` — ${data.message}` : ""}`);
  showTransactionLink(data.txHash);
  return data;
}

$("loginForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try { await login(); } catch (error) { message("authStatus", error.message); }
});

$("logoutButton").addEventListener("click", async () => {
  try { await apiRequest("/api/auth/logout", { method: "POST", body: "{}" }); } finally { csrfToken = null; currentUser = null; renderUser(null); }
});

$("connectButton").addEventListener("click", async () => {
  try { await connectWallet(); } catch (error) { message("walletStatus", error.message); }
});

$("transferForm").addEventListener("submit", async (event) => {
  event.preventDefault(); $("sendButton").disabled = true;
  try {
    if (!connectedAddress) await connectWallet();
    const intent = await apiRequest("/api/transfers/prepare", { method: "POST", body: JSON.stringify({ sender: connectedAddress, recipient: $("recipient").value.trim(), amount: $("amount").value.trim() }) });
    const provider = new ethers.BrowserProvider(window.ethereum);
    const signer = await provider.getSigner();
    const tx = await signer.sendTransaction({ to: $("recipient").value.trim(), value: ethers.parseEther($("amount").value.trim()) });
    localStorage.setItem(LAST_TRANSFER_KEY, JSON.stringify({ id: intent.id, txHash: tx.hash }));
    message("transferStatus", "Transaction submitted; waiting for confirmation."); showTransactionLink(tx.hash);
    for (let attempt = 0; attempt < 10; attempt++) {
      const result = await verifyEthTransfer(intent.id, tx.hash);
      if (["confirmed", "failed"].includes(result.status)) break;
      await new Promise(resolve => setTimeout(resolve, 7000));
    }
  } catch (error) { message("transferStatus", error.message); } finally { $("sendButton").disabled = false; }
});

$("distributionForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    if (!connectedAddress) await connectWallet();
    const prepared = await apiRequest("/api/admin/distributions/prepare", { method: "POST", body: JSON.stringify({ recipientAddress: $("tokenRecipient").value.trim(), amount: $("tokenAmount").value.trim() }) });
    const provider = new ethers.BrowserProvider(window.ethereum);
    const signer = await provider.getSigner();
    const contract = new ethers.Contract(prepared.contract, ["function transfer(address to, uint256 amount) returns (bool)"], signer);
    const units = ethers.parseUnits($("tokenAmount").value.trim(), 18);
    const tx = await contract.transfer($("tokenRecipient").value.trim(), units);
    message("adminStatus", `PTC transaction submitted: ${tx.hash}`);
    const result = await apiRequest(`/api/admin/distributions/${encodeURIComponent(prepared.id)}/verify`, { method: "POST", body: JSON.stringify({ txHash: tx.hash }) });
    message("adminStatus", `PTC distribution status: ${result.status}. Contract policy is enforced on-chain.`);
  } catch (error) { message("adminStatus", error.message); }
});

$("auditButton").addEventListener("click", async () => {
  try {
    const data = await apiRequest("/api/admin/audit-logs?limit=100");
    const output = $("auditOutput"); output.textContent = JSON.stringify(data.logs, null, 2); output.hidden = false;
  } catch (error) { message("adminStatus", error.message); }
});

loadSession();
    
