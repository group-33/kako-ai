import {
  ArrowDownIcon,
  ArrowUpIcon,
  CheckIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CopyIcon,
  PencilIcon,
  RefreshCwIcon,
  Square,
} from "lucide-react";

import {
  ActionBarPrimitive,
  BranchPickerPrimitive,
  ComposerPrimitive,
  ErrorPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useAssistantApi,
  useAssistantState,
} from "@assistant-ui/react";

import type { FC } from "react";
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

const Composer: FC<{ threadId: string; initialDraft?: string }> = ({ threadId, initialDraft }) => {
  const { t } = useTranslation();
  const api = useAssistantApi();
  const appliedDraftRef = useRef(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const composerText = useAssistantState(({ composer }) => composer.text);
  const { drafts, setDraft } = useChatStore();
  const lastSavedRef = useRef<string | null>(null);
  const hasInitializedRef = useRef(false);
  const prevComposerTextRef = useRef("");
  const storedDraft = drafts[threadId];
  const effectiveDraft = storedDraft ?? initialDraft;

  useEffect(() => {
    if (!effectiveDraft) return;

    const applyDraft = () => {
      if (appliedDraftRef.current) return;
      const currentText = api.composer().getState().text;
      if (currentText.trim()) return;
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
      appliedDraftRef.current = true;
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
    if (!composerText && storedDraft && !clearedByUser) return;
    if (lastSavedRef.current === composerText) return;
    lastSavedRef.current = composerText;
    setDraft(threadId, composerText);
    prevComposerTextRef.current = composerText;
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


export const Thread: FC<{ threadId: string; initialDraft?: string }> = ({ threadId, initialDraft }) => {
  return (
    <ThreadPrimitive.Root
      className="aui-root aui-thread-root @container flex h-full flex-col bg-transparent"
      style={{
        ["--thread-max-width" as string]: "44rem",
      }}
    >
      <ThreadPrimitive.Viewport
        turnAnchor="top"
        className="aui-thread-viewport relative flex flex-1 flex-col overflow-x-auto overflow-y-scroll scroll-smooth px-4 pt-4"
      >
        <ThreadPrimitive.If empty>
          <ThreadWelcome />
        </ThreadPrimitive.If>

        <ThreadPrimitive.Messages
          components={{
            UserMessage,
            EditComposer,
            AssistantMessage,
          }}
        />

        <ThreadPrimitive.ViewportFooter className="aui-thread-viewport-footer sticky bottom-0 mx-auto mt-4 flex w-full max-w-(--thread-max-width) flex-col gap-4 overflow-visible rounded-t-3xl bg-[#090e20] pb-4 md:pb-6">
          <ThreadScrollToBottom />
          <Composer threadId={threadId} initialDraft={initialDraft} />
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
    <div className="aui-thread-welcome-root mx-auto my-auto flex w-full max-w-(--thread-max-width) grow flex-col">
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
      <ThreadSuggestions />
    </div>
  );
};

const ThreadSuggestions: FC = () => {
  const { t } = useTranslation();
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
          <ThreadPrimitive.Suggestion
            prompt={suggestedAction.action}
            send
            asChild
          >
            <Button
              variant="ghost"
              className="aui-thread-welcome-suggestion h-auto w-full flex-1 @md:flex-col flex-wrap items-start justify-start gap-1 rounded-2xl border border-slate-800 bg-slate-900/50 px-5 py-4 text-left text-sm hover:bg-slate-800 hover:border-indigo-500/30 transition-all shadow-sm"
              aria-label={suggestedAction.action}
            >
              <span className="aui-thread-welcome-suggestion-text-1 font-medium text-slate-200">
                {suggestedAction.title}
              </span>
              <span className="aui-thread-welcome-suggestion-text-2 text-slate-500">
                {suggestedAction.label}
              </span>
            </Button>
          </ThreadPrimitive.Suggestion>
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
        <AssistantActionBar />
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


const AssistantActionBar: FC = () => {
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      autohideFloat="single-branch"
      className="aui-assistant-action-bar-root -ml-1 col-start-3 row-start-2 flex gap-1 text-muted-foreground data-floating:absolute data-floating:rounded-md data-floating:border data-floating:bg-background data-floating:p-1 data-floating:shadow-sm"
    >
      <ActionBarPrimitive.Copy asChild>
        <TooltipIconButton tooltip="Copy">
          <MessagePrimitive.If copied>
            <CheckIcon />
          </MessagePrimitive.If>
          <MessagePrimitive.If copied={false}>
            <CopyIcon />
          </MessagePrimitive.If>
        </TooltipIconButton>
      </ActionBarPrimitive.Copy>
      <ActionBarPrimitive.Reload asChild>
        <TooltipIconButton tooltip="Refresh">
          <RefreshCwIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.Reload>
    </ActionBarPrimitive.Root>
  );
};

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
        <div className="aui-user-action-bar-wrapper -translate-x-full -translate-y-1/2 absolute top-1/2 left-0 pr-2">
          <UserActionBar />
        </div>
      </div>

      <BranchPicker className="aui-user-branch-picker -mr-1 col-span-full col-start-1 row-start-3 justify-end" />
    </MessagePrimitive.Root>
  );
};

const UserActionBar: FC = () => {
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      className="aui-user-action-bar-root flex flex-col items-end"
    >
      <ActionBarPrimitive.Edit asChild>
        <TooltipIconButton tooltip="Edit" className="aui-user-action-edit p-4">
          <PencilIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.Edit>
    </ActionBarPrimitive.Root>
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
