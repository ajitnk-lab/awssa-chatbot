#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { AwsReposAgentStack } from './lib/cdk-stack';

const app = new cdk.App();
new AwsReposAgentStack(app, 'AwsReposAgentStack', {
  env: {
    region: 'us-west-2'
  }
});
