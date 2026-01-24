import React from 'react';
import { X } from 'lucide-react';

interface LegalModalProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    content: string;
    closeLabel?: string;
}

export const LegalModal: React.FC<LegalModalProps> = ({ isOpen, onClose, title, content, closeLabel = "Close" }) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
            <div
                className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl animate-in zoom-in-95 duration-200"
                role="dialog"
                aria-modal="true"
            >
                <div className="flex items-center justify-between p-6 border-b border-slate-800">
                    <h2 className="text-xl font-semibold text-slate-100">{title}</h2>
                    <button
                        onClick={onClose}
                        className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                        aria-label="Close"
                    >
                        <X size={20} />
                    </button>
                </div>

                <div className="p-6 overflow-y-auto custom-scrollbar text-slate-300 space-y-4 max-h-[60vh]">
                    {content.split('\n\n').map((block, index) => {
                        const trimmed = block.trim();
                        if (trimmed.startsWith('#')) {
                            return <h3 key={index} className="text-lg font-bold text-white mt-6 first:mt-0 mb-2">{trimmed.replace(/^#\s*/, '')}</h3>;
                        }

                        return (
                            <div key={index} className="text-sm leading-relaxed text-slate-300">
                                {trimmed.split('\n').map((line, lineIndex) => (
                                    <div key={lineIndex} className={line.trim().startsWith('-') ? 'pl-4 flex mb-1' : 'mb-1'}>
                                        {line.split(/(\*\*.*?\*\*)/).map((part, partIndex) => {
                                            if (part.startsWith('**') && part.endsWith('**')) {
                                                return <strong key={partIndex} className="text-slate-100 font-semibold">{part.slice(2, -2)}</strong>;
                                            }
                                            return <span key={partIndex}>{part}</span>;
                                        })}
                                    </div>
                                ))}
                            </div>
                        );
                    })}
                </div>

                <div className="p-6 border-t border-slate-800 flex justify-end">
                    <button
                        onClick={onClose}
                        className="bg-slate-100 hover:bg-white text-slate-900 font-medium px-4 py-2 rounded-lg transition-colors"
                    >
                        {closeLabel}
                    </button>
                </div>
            </div>
        </div>
    );
};
