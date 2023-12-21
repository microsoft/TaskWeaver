import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'Support Rich Data Structure',
    Svg: require('@site/static/img/data.jpg').default,
    description: (
      <>
        TaskWeaver is designed to support rich data structure
         (e.g., <code>pandas DataFrame</code>) in a stateful manner through the conversation.
      </>
    ),
  },
  {
    title: 'Plugin Powered',
    Svg: require('@site/static/img/plugins.jpg').default,
    description: (
      <>
        TaskWeaver leverages customized <code>plugins</code> to extend the functionality 
        of the Agent while supporting ad-hoc user queries.
      </>
    ),
  },
  
  {
    title: 'Incorporate Domain Knowledge',
    Svg: require('@site/static/img/domains.jpg').default,
    description: (
      <>
        Extend or customize your own Agent by incorporating Plugins and various 
        Examples for domain-specific scenarios.
      </>
    ),
  },
];

function Feature({Svg, title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <img src={Svg} className={styles.featureSvg}/>
        {/* <Svg className={styles.featureSvg} role="img" /> */}
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
