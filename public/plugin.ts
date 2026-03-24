type AppRegistration = {
  id: string;
  title: string;
  category: { id: string; label: string; order: number };
  mount: (params: { element: HTMLElement }) => Promise<() => void>;
};

type CoreLike = {
  application: {
    register: (app: AppRegistration) => void;
    navigateToApp: (appId: string) => Promise<void>;
  };
};

function render(host: HTMLElement, navigateToApp: (appId: string) => Promise<void>) {
  host.innerHTML = [
    '<div style="padding:24px;font-family:Inter,Segoe UI,Arial,sans-serif;max-width:960px;">',
    '<h1 style="margin:0 0 8px;">XDR Security</h1>',
    '<p style="margin:0 0 18px;color:#4b5563;">Unified entry point for XDR Coordinator and XDR Defense plugins.</p>',
    '<div style="display:flex;gap:12px;flex-wrap:wrap;">',
    '<button id="xdr-open-coordinator" style="padding:10px 14px;border:1px solid #0f62fe;background:#0f62fe;color:#fff;border-radius:6px;cursor:pointer;">Open XDR Coordinator</button>',
    '<button id="xdr-open-defense" style="padding:10px 14px;border:1px solid #1f2937;background:#1f2937;color:#fff;border-radius:6px;cursor:pointer;">Open XDR Defense</button>',
    '</div>',
    '</div>'
  ].join('');

  const coordinator = host.querySelector('#xdr-open-coordinator') as HTMLButtonElement | null;
  const defense = host.querySelector('#xdr-open-defense') as HTMLButtonElement | null;

  if (coordinator) {
    coordinator.addEventListener('click', () => {
      void navigateToApp('xdrCoordinator');
    });
  }

  if (defense) {
    defense.addEventListener('click', () => {
      void navigateToApp('xdrDefense');
    });
  }
}

export function createXdrSecurityPlugin() {
  return {
    setup(core: CoreLike) {
      core.application.register({
        id: 'xdrSecurity',
        title: 'XDR Security',
        category: {
          id: 'xdrSecurity',
          label: 'XDR Security',
          order: 2200,
        },
        mount: (params: { element: HTMLElement }) => {
          render(params.element, core.application.navigateToApp);
          return Promise.resolve(() => {
            params.element.innerHTML = '';
          });
        },
      });

      return {};
    },

    start() {
      return {};
    },

    stop() {},
  };
}
