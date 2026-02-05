import {
  ArrowDownIcon,
  ArrowUpIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  Square,
} from "lucide-react";

import {
  BranchPickerPrimitive,
  ComposerPrimitive,
  ErrorPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useAssistantApi,
  useAssistantState,
} from "@assistant-ui/react";

import type { FC, RefObject } from "react";
import { useEffect, useRef } from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { MarkdownText } from "@/components/assistant-ui/markdown-text";
import { ToolFallback } from "@/components/assistant-ui/tool-fallback";
import { TooltipIconButton } from "@/components/assistant-ui/tooltip-icon-button";
import {
  ComposerAddAttachment,
  ComposerAttachments,
  UserMessageAttachments,
} from "@/components/assistant-ui/attachment";

import { cn } from "@/lib/utils";
import { useChatStore } from "@/store/useChatStore";

import { useTranslation } from "react-i18next";

const Composer: FC<{ 
  threadId: string; 
  initialDraft?: string; 
  textareaRef: RefObject<HTMLTextAreaElement | null> // Added | null
}> = ({
  threadId,
  initialDraft,
  textareaRef,
}) => {
  const { t } = useTranslation();
  const api = useAssistantApi();
  const lastAppliedDraftRef = useRef<string | null>(null);
  const composerText = useAssistantState(({ composer }) => composer.text);
  const setDraft = useChatStore(s => s.setDraft);
  const storedDraft = useChatStore(s => s.drafts[threadId]);
  const lastSavedRef = useRef<string | null>(null);
  const hasInitializedRef = useRef(false);
  const prevComposerTextRef = useRef("");
  const effectiveDraft = storedDraft ?? initialDraft;

  useEffect(() => {
    lastAppliedDraftRef.current = null;
    lastSavedRef.current = null;
    prevComposerTextRef.current = "";
    hasInitializedRef.current = false;
  }, [threadId]);

  useEffect(() => {
    if (!effectiveDraft) return;

    const applyDraft = () => {
      if (lastAppliedDraftRef.current === effectiveDraft) return;
      const currentText = api.composer().getState().text;
      const hasText = currentText.trim().length > 0;
      const canReplace =
        lastAppliedDraftRef.current && currentText === lastAppliedDraftRef.current;
      if (hasText && !canReplace) return;
      api.composer().setText(effectiveDraft);
      requestAnimationFrame(() => {
        const textarea = textareaRef.current;
        if (!textarea) return;
        const start = effectiveDraft.indexOf("[");
        const end = effectiveDraft.indexOf("]");
        if (start !== -1 && end > start) {
          textarea.focus();
          textarea.setSelectionRange(start, end + 1);
        }
      });
      lastAppliedDraftRef.current = effectiveDraft;
    };

    const timeoutId = window.setTimeout(applyDraft, 0);
    const unsubscribe = api.on("thread-list-item.switched-to", applyDraft);

    return () => {
      window.clearTimeout(timeoutId);
      unsubscribe?.();
    };
  }, [api, effectiveDraft]);

  useEffect(() => {
    if (!threadId) return;
    if (!hasInitializedRef.current) {
      hasInitializedRef.current = true;
      if (!composerText && storedDraft) return;
    }
    const prevText = prevComposerTextRef.current;
    const clearedByUser = prevText && !composerText;

    // Update tracking ref immediately for logical consistency across renders
    prevComposerTextRef.current = composerText;

    if (!composerText && storedDraft && !clearedByUser) return;
    if (lastSavedRef.current === composerText) return;

    // Debounce the store update to prevent input frame drops
    const handler = setTimeout(() => {
      lastSavedRef.current = composerText;
      setDraft(threadId, composerText);
    }, 1000);

    return () => clearTimeout(handler);
  }, [composerText, setDraft, storedDraft, threadId]);

  return (
    <ComposerPrimitive.Root className="aui-composer-root relative flex w-full flex-col">
      <ComposerPrimitive.AttachmentDropzone className="aui-composer-attachment-dropzone flex w-full flex-col rounded-3xl border border-input bg-background px-1 pt-2 shadow-xs outline-none transition-[color,box-shadow] has-[textarea:focus-visible]:border-ring has-[textarea:focus-visible]:ring-[3px] has-[textarea:focus-visible]:ring-ring/50 data-[dragging=true]:border-ring data-[dragging=true]:border-dashed data-[dragging=true]:bg-accent/50 dark:bg-background">
        <ComposerAttachments />
        <ComposerPrimitive.Input
          placeholder={t('thread.composer.placeholder')}
          className="aui-composer-input mb-1 max-h-32 min-h-16 w-full resize-none bg-transparent px-3.5 pt-1.5 pb-3 text-base outline-none placeholder:text-muted-foreground focus-visible:ring-0"
          rows={1}
          autoFocus
          aria-label="Message input"
          ref={textareaRef}
        />
        <ComposerAction />
      </ComposerPrimitive.AttachmentDropzone>
    </ComposerPrimitive.Root>
  );
};


import { MessageProvider } from "@assistant-ui/react";

const VirtualMessageList: FC = () => {
  const messages = useAssistantState((state) => state.thread.messages);
  const scrollRef = useRef<HTMLDivElement>(null);
  const isAtBottomRef = useRef(true);

  useEffect(() => {
    const element = scrollRef.current;
    if (!element) return;

    const onScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = element;
      const distanceToBottom = scrollHeight - scrollTop - clientHeight;
      isAtBottomRef.current = distanceToBottom < 50;
    };

    element.addEventListener("scroll", onScroll);
    return () => element.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (scrollRef.current && isAtBottomRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div
      ref={scrollRef}
      className="w-full h-full overflow-y-auto px-4"
      style={{ overflowAnchor: "none", scrollBehavior: "smooth" }}
    >
      <div className="flex flex-col gap-5 pt-4 pb-1">
        {messages.map((message, index) => {
          const isUser = message.role === "user";
          const isEditing = isUser && !!message.composer?.isEditing;

          return (
            <MessageProvider
              key={message.id}
              message={message}
              index={index}
              isLast={index === messages.length - 1}
            >
              {isEditing ? <EditComposer /> : isUser ? <UserMessage /> : <AssistantMessage />}
            </MessageProvider>
          );
        })}
      </div>
    </div>
  );
};

export const Thread: FC<{ threadId: string; initialDraft?: string }> = ({ threadId, initialDraft }) => {
  const composerTextareaRef = useRef<HTMLTextAreaElement>(null);
  return (
    <ThreadPrimitive.Root
      className="aui-root aui-thread-root @container flex h-full flex-col bg-transparent"
      style={{
        ["--thread-max-width" as string]: "44rem",
      }}
    >
      <ThreadPrimitive.Viewport
        className="aui-thread-viewport relative flex flex-1 flex-col overflow-hidden px-4 pt-4"
      >
        <ThreadPrimitive.If empty>
          <ThreadWelcome />
        </ThreadPrimitive.If>

        {/* We use VirtualMessageList which handles the scrolling */}
        <div className="flex-1 w-full relative min-h-0">
          <VirtualMessageList />
        </div>

        <ThreadPrimitive.ViewportFooter className="aui-thread-viewport-footer sticky bottom-0 mx-auto mt-2 flex w-full max-w-(--thread-max-width) flex-col gap-4 overflow-visible rounded-t-3xl bg-[#090e20] pb-4 md:pb-6">
          <ThreadScrollToBottom />
          <ThreadPrimitive.If empty>
            <ThreadSuggestions threadId={threadId} textareaRef={composerTextareaRef} />
          </ThreadPrimitive.If>
          <Composer threadId={threadId} initialDraft={initialDraft} textareaRef={composerTextareaRef} />
        </ThreadPrimitive.ViewportFooter>
      </ThreadPrimitive.Viewport>
    </ThreadPrimitive.Root>
  );
};

const ThreadScrollToBottom: FC = () => {
  return (
    <ThreadPrimitive.ScrollToBottom asChild>
      <TooltipIconButton
        tooltip="Scroll to bottom"
        variant="outline"
        className="aui-thread-scroll-to-bottom -top-12 absolute z-10 self-center rounded-full p-4 disabled:invisible dark:bg-background dark:hover:bg-accent"
      >
        <ArrowDownIcon />
      </TooltipIconButton>
    </ThreadPrimitive.ScrollToBottom>
  );
};

const ThreadWelcome: FC = () => {
  const { t } = useTranslation();
  return (
    <div className="aui-thread-welcome-root mx-auto my-auto flex w-full max-w-(--thread-max-width) grow flex-col pt-21">
      <div className="aui-thread-welcome-center flex w-full grow flex-col items-center justify-center">
        <div className="aui-thread-welcome-message flex size-full flex-col justify-center px-8">
          <div className="aui-thread-welcome-message-inner fade-in slide-in-from-bottom-2 animate-in font-semibold text-2xl duration-300 ease-out">
            {t('thread.welcome.title')}
          </div>
          <div className="aui-thread-welcome-message-inner fade-in slide-in-from-bottom-2 animate-in text-2xl text-muted-foreground/65 delay-100 duration-300 ease-out">
            {t('thread.welcome.message')}
          </div>
        </div>
      </div>
    </div>
  );
};

const ThreadSuggestions: FC<{ 
  threadId: string; 
  textareaRef: RefObject<HTMLTextAreaElement | null> // Added | null
}> = ({
  threadId,
  textareaRef,
}) => {
  const { t } = useTranslation();
  const api = useAssistantApi();
  const setDraft = useChatStore(s => s.setDraft);
  const isDisabled = useAssistantState(({ thread }) => thread.isDisabled);
  const handleSuggestionClick = (prompt: string) => {
    if (isDisabled) return;
    api.composer().setText(prompt);
    setDraft(threadId, prompt);
    requestAnimationFrame(() => {
      const textarea = textareaRef.current;
      if (!textarea) return;
      const start = prompt.indexOf("[");
      const end = prompt.indexOf("]");
      textarea.focus();
      if (start !== -1 && end > start) {
        textarea.setSelectionRange(start, end + 1);
      } else {
        textarea.setSelectionRange(prompt.length, prompt.length);
      }
    });
  };
  return (
    <div className="aui-thread-welcome-suggestions grid w-full @md:grid-cols-2 gap-2 pb-4">
      {[
        {
          title: t('thread.suggestions.createBom.title'),
          label: t('thread.suggestions.createBom.label'),
          action: t('thread.suggestions.createBom.action'),
        },
        {
          title: t('thread.suggestions.checkInventory.title'),
          label: t('thread.suggestions.checkInventory.label'),
          action: t('thread.suggestions.checkInventory.action'),
        },
        {
          title: t('thread.suggestions.optimizeProcurement.title'),
          label: t('thread.suggestions.optimizeProcurement.label'),
          action: t('thread.suggestions.optimizeProcurement.action'),
        },
        {
          title: t('thread.suggestions.compareSuppliers.title'),
          label: t('thread.suggestions.compareSuppliers.label'),
          action: t('thread.suggestions.compareSuppliers.action'),
        },
      ].map((suggestedAction, index) => (
        <div
          key={`suggested-action-${index}`}
          className="aui-thread-welcome-suggestion-display fade-in slide-in-from-bottom-4 @md:nth-[n+3]:block nth-[n+3]:hidden animate-in fill-mode-both duration-300 ease-out"
          style={{ animationDelay: `${index * 50}ms` }}
        >
          <Button
            variant="ghost"
            className="aui-thread-welcome-suggestion h-auto w-full flex-1 @md:flex-col flex-wrap items-start justify-start gap-1 rounded-2xl border border-slate-800 bg-slate-900/50 px-5 py-4 text-left text-sm hover:bg-slate-800 hover:border-indigo-500/30 transition-all shadow-sm"
            aria-label={suggestedAction.action}
            onClick={() => handleSuggestionClick(suggestedAction.action)}
            disabled={isDisabled}
          >
            <span className="aui-thread-welcome-suggestion-text-1 font-medium text-slate-200">
              {suggestedAction.title}
            </span>
            <span className="aui-thread-welcome-suggestion-text-2 text-slate-500">
              {suggestedAction.label}
            </span>
          </Button>
        </div>
      ))}
    </div>
  );
};

const ComposerAction: FC = () => {
  return (
    <div className="aui-composer-action-wrapper relative mx-1 mt-2 mb-2 flex items-center justify-between">
      <ComposerAddAttachment />

      <ThreadPrimitive.If running={false}>
        <ComposerPrimitive.Send asChild>
          <TooltipIconButton
            tooltip="Send message"
            side="bottom"
            type="submit"
            variant="default"
            size="icon"
            className="aui-composer-send size-[34px] rounded-full p-1"
            aria-label="Send message"
          >
            <ArrowUpIcon className="aui-composer-send-icon size-5" />
          </TooltipIconButton>
        </ComposerPrimitive.Send>
      </ThreadPrimitive.If>

      <ThreadPrimitive.If running>
        <ComposerPrimitive.Cancel asChild>
          <Button
            type="button"
            variant="default"
            size="icon"
            className="aui-composer-cancel size-[34px] rounded-full border border-muted-foreground/60 hover:bg-primary/75 dark:border-muted-foreground/90"
            aria-label="Stop generating"
          >
            <Square className="aui-composer-cancel-icon size-3.5 fill-white dark:fill-black" />
          </Button>
        </ComposerPrimitive.Cancel>
      </ThreadPrimitive.If>
    </div>
  );
};


const MessageError: FC = () => {
  return (
    <MessagePrimitive.Error>
      <ErrorPrimitive.Root className="aui-message-error-root mt-2 rounded-md border border-destructive bg-destructive/10 p-3 text-destructive text-sm dark:bg-destructive/5 dark:text-red-200">
        <ErrorPrimitive.Message className="aui-message-error-message line-clamp-2" />
      </ErrorPrimitive.Root>
    </MessagePrimitive.Error>
  );
};

const AssistantMessage: FC = () => {
  const message = useAssistantState(({ message }) => message);
  const isRunning = useAssistantState(({ thread }) => thread.isRunning);
  const messages = useAssistantState(({ thread }) => thread.messages);

  const isLast = messages[messages.length - 1]?.id === message.id;
  const hasContent = message.content && message.content.length > 0;
  const showThinking = isRunning && isLast && !hasContent;

  return (
    <MessagePrimitive.Root
      className="aui-assistant-message-root fade-in slide-in-from-bottom-1 relative mx-auto w-full max-w-(--thread-max-width) animate-in py-4 duration-150 ease-out"
      data-role="assistant"
    >
      <div className="aui-assistant-message-content wrap-break-word mx-2 text-foreground leading-7">
        <div className="flex flex-col gap-4">
          <MessagePrimitive.Parts
            components={{
              Text: MarkdownText,
              tools: { Fallback: ToolFallback },
            }}
          />
        </div>

        {showThinking && (
          <div className="flex flex-col gap-2 mt-2">
            <ThinkingMessage />
          </div>
        )}

        <MessageError />
      </div>

      <div className="aui-assistant-message-footer mt-2 ml-2 flex">
        <BranchPicker />
      </div>
    </MessagePrimitive.Root>
  );
};

const ThinkingMessage = () => {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col gap-2 animate-pulse w-full max-w-md">
      <div className="flex items-center gap-2 mb-1">
        <div className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: "0ms" }} />
        <div className="w-2 h-2 rounded-full bg-purple-500 animate-bounce" style={{ animationDelay: "150ms" }} />
        <div className="w-2 h-2 rounded-full bg-pink-500 animate-bounce" style={{ animationDelay: "300ms" }} />
        <span className="text-xs font-medium text-slate-500 ml-2">{t('thread.message.thinking')}</span>
      </div>
      <Skeleton className="h-4 w-3/4 rounded-lg bg-slate-800/30" />
      <Skeleton className="h-4 w-1/2 rounded-lg bg-slate-800/30" />
    </div>
  )
}




const UserMessage: FC = () => {
  return (
    <MessagePrimitive.Root
      className="aui-user-message-root fade-in slide-in-from-bottom-1 mx-auto grid w-full max-w-(--thread-max-width) animate-in auto-rows-auto grid-cols-[minmax(72px,1fr)_auto] content-start gap-y-2 px-2 py-4 duration-150 ease-out [&:where(>*)]:col-start-2"
      data-role="user"
    >
      <UserMessageAttachments />

      <div className="aui-user-message-content-wrapper relative col-start-2 min-w-0">
        <div className="aui-user-message-content wrap-break-word rounded-3xl bg-muted px-5 py-2.5 text-foreground">
          <MessagePrimitive.Parts />
        </div>
      </div>

      <BranchPicker className="aui-user-branch-picker -mr-1 col-span-full col-start-1 row-start-3 justify-end" />
    </MessagePrimitive.Root>
  );
};



const EditComposer: FC = () => {
  const { t } = useTranslation();
  return (
    <MessagePrimitive.Root className="aui-edit-composer-wrapper mx-auto flex w-full max-w-(--thread-max-width) flex-col gap-4 px-2">
      <ComposerPrimitive.Root className="aui-edit-composer-root ml-auto flex w-full max-w-7/8 flex-col rounded-xl bg-muted">
        <ComposerPrimitive.Input
          className="aui-edit-composer-input flex min-h-[60px] w-full resize-none bg-transparent p-4 text-foreground outline-none"
          autoFocus
        />

        <div className="aui-edit-composer-footer mx-3 mb-3 flex items-center justify-center gap-2 self-end">
          <ComposerPrimitive.Cancel asChild>
            <Button variant="ghost" size="sm" aria-label="Cancel edit">
              {t('thread.composer.cancel')}
            </Button>
          </ComposerPrimitive.Cancel>
          <ComposerPrimitive.Send asChild>
            <Button size="sm" aria-label="Update message">
              {t('thread.composer.update')}
            </Button>
          </ComposerPrimitive.Send>
        </div>
      </ComposerPrimitive.Root>
    </MessagePrimitive.Root>
  );
};

const BranchPicker: FC<BranchPickerPrimitive.Root.Props> = ({
  className,
  ...rest
}) => {
  return (
    <BranchPickerPrimitive.Root
      hideWhenSingleBranch
      className={cn(
        "aui-branch-picker-root -ml-2 mr-2 inline-flex items-center text-muted-foreground text-xs",
        className,
      )}
      {...rest}
    >
      <BranchPickerPrimitive.Previous asChild>
        <TooltipIconButton tooltip="Previous">
          <ChevronLeftIcon />
        </TooltipIconButton>
      </BranchPickerPrimitive.Previous>
      <span className="aui-branch-picker-state font-medium">
        <BranchPickerPrimitive.Number /> / <BranchPickerPrimitive.Count />
      </span>
      <BranchPickerPrimitive.Next asChild>
        <TooltipIconButton tooltip="Next">
          <ChevronRightIcon />
        </TooltipIconButton>
      </BranchPickerPrimitive.Next>
    </BranchPickerPrimitive.Root>
  );
};
