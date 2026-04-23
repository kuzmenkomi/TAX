import { ConnectButton } from '@rainbow-me/rainbowkit';

export default function WalletConnectButton() {
  return (
    <div className="flex justify-center">
      <ConnectButton 
        label="Connect with MetaMask"
        showBalance={false}
        chainStatus="icon"
        accountStatus="address"
      />
    </div>
  );
}
